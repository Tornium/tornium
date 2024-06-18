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

#include <unistd.h>

#include <boost/asio/io_context.hpp>
#include <boost/asio/placeholders.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/bind/bind.hpp>
#include <cxxopts.hpp>
#include <string>
#include <thread>

#include "args.h"
#include "config.h"
#include "datagram_server.h"
#include "http.h"
#include "request_queue.h"

int main(int argc, char *argv[]) {
    scheduler::config config_;
    scheduler::parse_args(argc, argv, config_);

    ::unlink(config_.socket_path.c_str());
    boost::asio::io_context io_context_;
    scheduler::DatagramServer s_(io_context_, config_);
    s_.do_receive();

    std::thread http_thread(scheduler::start_curl_uv_loop);

    boost::asio::steady_timer queue_timer(io_context_, boost::asio::chrono::seconds(10));
    queue_timer.async_wait(
        boost::bind(scheduler::queue_processing_work, boost::asio::placeholders::error, &queue_timer));

    io_context_.run();

    return 0;
}
