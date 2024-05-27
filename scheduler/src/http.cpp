// Copyright 2024 tiksan
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "http.h"

#include <curl/curl.h>
#include <unistd.h>
#include <uv.h>

#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <ostream>
#include <string>

#include "request.h"

// Contains one or more handlers for the individual transfers
static CURLM *curl_handler;

// Default loop provided by libuv
//
// https://docs.libuv.org/en/v1.x/guide/basics.html#default-loop
static uv_loop_t *event_loop;

// Timer used for socket timeouts
//
// https://docs.libuv.org/en/v1.x/guide/utilities.html#timers
static uv_timer_t timeout_timer;

typedef struct curl_context_s {
    uv_poll_t poll_handle;
    curl_socket_t socket_fd;
} curl_context_t;

struct response {
    char *memory;
    size_t size;
    scheduler::Request *request_;
};

void after_process_http_response(uv_work_t *work, int /*status*/) {
    free(work->data);
    free(work);
    exit(0);
    return;
}

void process_http_response(uv_work_t *work) {
    std::string body_buffer(((scheduler::http_response *)work->data)->response_body);
    std::cout << body_buffer << std::endl;
    return;
}

size_t on_write_callback(char *contents, size_t size, size_t number_megabytes, void *userp) {
    std::string endpoint = std::string(((struct response *)userp)->request_->endpoint);
    std::cout << "Received response from " << endpoint << std::endl;

    scheduler::http_response *response_ = (scheduler::http_response *)malloc(sizeof(scheduler::http_response));
    response_->response_body = contents;

    uv_work_t *work = (uv_work_t *)malloc(sizeof(uv_work_t));
    work->data = response_;
    uv_queue_work(event_loop, work, process_http_response, after_process_http_response);

    delete ((struct response *) userp)->request_;
    free(userp);

    return size * number_megabytes;
}

void scheduler::emplace_http_requeset(scheduler::Request *request_) {
    // Handle to the transfer
    CURL *handle = curl_easy_init();

    // Black hole the data normally passed to stdout or a file pointer
    // struct response void_chunk = {.memory=(char*) malloc(0), .size=0};
    struct response *response_chunk = (struct response *)malloc(sizeof(response));
    response_chunk->memory = (char *)malloc(0);
    response_chunk->size = 0;
    response_chunk->request_ = request_;

    // Add various options to the handle for the transfer
    // https://everything.curl.dev/transfers/options/index.html
    curl_easy_setopt(handle, CURLOPT_URL, request_ -> endpoint.c_str());
    curl_easy_setopt(handle, CURLOPT_TIMEOUT_MS, 5000L);
    curl_easy_setopt(handle, CURLOPT_WRITEFUNCTION, on_write_callback);
    curl_easy_setopt(handle, CURLOPT_WRITEDATA, response_chunk);

    curl_multi_add_handle(curl_handler, handle);
    return;
}

void check_multi_info() {
    char *completed_request_url;
    CURLMsg *message;
    int pending;

    while ((message = curl_multi_info_read(curl_handler, &pending))) {
        switch (message->msg) {
            case CURLMSG_DONE:
                curl_easy_getinfo(message->easy_handle, CURLINFO_EFFECTIVE_URL, &completed_request_url);

                curl_multi_remove_handle(curl_handler, message->easy_handle);
                curl_easy_cleanup(message->easy_handle);
                break;
            default:
                abort();
        }
    }
}

void curl_perform(uv_poll_t *req, int status, int events) {
    uv_timer_stop(&timeout_timer);
    int running_handles;
    int flags = 0;
    if (status < 0) flags = CURL_CSELECT_ERR;
    if (!status && events & UV_READABLE) flags |= CURL_CSELECT_IN;
    if (!status && events & UV_WRITABLE) flags |= CURL_CSELECT_OUT;

    curl_context_t *context;
    context = (curl_context_t *)req;

    curl_multi_socket_action(curl_handler, context->socket_fd, flags, &running_handles);
    check_multi_info();
}

curl_context_t *create_curl_context(curl_socket_t socket_fd) {
    curl_context_t *context = (curl_context_t *)malloc(sizeof *context);
    context->socket_fd = socket_fd;

    uv_poll_init_socket(event_loop, &context->poll_handle, socket_fd);
    context->poll_handle.data = context;

    return context;
}

int curl_socket_callback_(CURL * /*handle*/, curl_socket_t socket_, int action,
                          void * /*clientp*/,  // Private callback pointer
                          void *socketp        // Private socket pointer
) {
    // https://curl.se/libcurl/c/CURLMOPT_SOCKETFUNCTION.html
    // https://docs.libuv.org/en/v1.x/guide/utilities.html#external-i-o-with-polling
    //
    // uv_poll_start: https://docs.libuv.org/en/v1.x/poll.html#c.uv_poll_start

    curl_context_t *curl_context;

    if (action == CURL_POLL_IN || action == CURL_POLL_OUT) {
        if (socketp) {
            curl_context = (curl_context_t *)socketp;
        } else {
            curl_context = create_curl_context(socket_);
            curl_multi_assign(curl_handler, socket_, (void *)curl_context);
        }
    }

    switch (action) {
        case CURL_POLL_IN:
            uv_poll_start(&curl_context->poll_handle, UV_READABLE, curl_perform);
            break;
        case CURL_POLL_OUT:
            uv_poll_start(&curl_context->poll_handle, UV_WRITABLE, curl_perform);
            break;
        case CURL_POLL_REMOVE:
            if (socketp) {
                uv_poll_stop(&((curl_context_t *)socketp)->poll_handle);
                curl_multi_assign(curl_handler, socket_, NULL);
            }

            break;
        default:
            abort();
    }

    return 0;
}

void on_socket_timeout(uv_timer_t * /*req*/) {
    int running_handles;
    curl_multi_socket_action(curl_handler, CURL_SOCKET_TIMEOUT, 0, &running_handles);
}

void curl_socket_timer(CURLM * /*multi*/, size_t timeout_milliseconds, void * /*userp*/) {
    if (timeout_milliseconds <= 0) {
        timeout_milliseconds = 1; /* 0 means directly call socket_action, but we'll do it in a bit */
    }

    uv_timer_start(&timeout_timer, on_socket_timeout, timeout_milliseconds, 0);
}

void idle_handle_callback(uv_idle_t * /*handle*/) {
    usleep(5);
    return;
}

void scheduler::start_curl_uv_loop() {
    // Curl global initialization is required
    // Especially to ensure that thread safety
    //
    // https://everything.curl.dev/libcurl/globalinit.html
    if (curl_global_init(CURL_GLOBAL_ALL)) {
        std::cerr << "Unable to init curl" << std::endl;
        exit(1);
    }

    event_loop = uv_default_loop();
    uv_timer_init(event_loop, &timeout_timer);

    // Handle to prevent uvloop from finishing when no requests are present
    uv_idle_t idler;
    uv_idle_init(event_loop, &idler);
    uv_idle_start(&idler, idle_handle_callback);

    std::cout << "event loop started" << std::endl;

    curl_handler = curl_multi_init();
    curl_multi_setopt(curl_handler, CURLMOPT_SOCKETFUNCTION, curl_socket_callback_);
    curl_multi_setopt(curl_handler, CURLMOPT_TIMERFUNCTION, curl_socket_timer);

    uv_run(event_loop, UV_RUN_DEFAULT);

    curl_multi_cleanup(curl_handler);
    return;
}
