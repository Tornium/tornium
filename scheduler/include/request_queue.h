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

#ifndef REQUEST_QUEUE_H
#define REQUEST_QUEUE_H

#include <boost/asio/steady_timer.hpp>

#include "request.h"

namespace scheduler {
/**
 * @brief Insert a request into the user's sorted vector of queued requests
 *
 * @param request_ Pointer to the request
 */
void queue_request(scheduler::Request* request_);

void queue_processing_work(const boost::system::error_code& error, boost::asio::steady_timer* queue_timer);
}  // namespace scheduler

#endif
