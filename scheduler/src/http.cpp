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
#include "cpr/api.h"
#include "cpr/session.h"
#include "request.h"
#include <boost/url/parse.hpp>
#include <boost/url/urls.hpp>
#include <chrono>
#include <cpr/cpr.h>

#include <iostream>
#include <memory>
#include <vector>

std::vector<std::unique_ptr<cpr::AsyncResponse>> pending_requests = {};

// Pre-allocate the memory for these objects
std::vector<std::unique_ptr<cpr::AsyncResponse>>::iterator request_iterator;
boost::url_view request_url;
const std::chrono::seconds request_wait_period = std::chrono::seconds{0};

void scheduler::emplace_http_requeset(scheduler::Request &request_) {
  cpr::Url url = cpr::Url(request_.endpoint);
  pending_requests.push_back(
      std::make_unique<cpr::AsyncResponse>(cpr::GetAsync(url)));

  std::cout << "Pending request count: " << pending_requests.size()
            << std::endl;
  return;
}

void scheduler::check_request() {
  std::cout << "Starting requests checks" << std::endl;

  do {
    // FIXME: For some reason, without a usleep here, the while loop has issues
    // checking values
    // TODO: Re-use sessions and connections
    usleep(5);

    request_iterator = pending_requests.begin();

    while (request_iterator != pending_requests.end()) {
      const auto pending_response = request_iterator->get();
      if (pending_response->valid() and
          pending_response->wait_for(request_wait_period) ==
              std::future_status::ready) {
        const cpr::Response response = pending_response->get();
        request_url =
            boost::url_view(boost::system::result<boost::url_view>(
                                boost::urls::parse_uri(response.url.str()))
                                .value());

        if (not response.error.message.empty()) {
          // TODO: Make sure that error checking is valid
          // TODO: Handle errors properly
          // TODO: Implement max retries into request class and retries into
          // logic
          std::cout << response.status_code << std::endl;
          std::cout << response.error.message << std::endl;

          std::optional<scheduler::Request> request_ =
              scheduler::request_by_path(request_url.path());

          if (request_ and !scheduler::retry_request(request_.value())) {
            // Request was not able to be retried as the number of retries would
            // be greater than the maximum number of retries specified for this
            // request.

            // TODO: Push this error to the queue
          }
        }

        request_iterator = pending_requests.erase(request_iterator);
        scheduler::remove_request(request_url.path());
        // TODO: Remove request in other places too
      } else {
        request_iterator++;
      }
    };
  } while (true);
}
