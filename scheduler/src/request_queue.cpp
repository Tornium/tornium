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

#include "request_queue.h"

#include <algorithm>
#include <boost/asio/detail/chrono.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/placeholders.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/bind.hpp>
#include <boost/bind/bind.hpp>
#include <iostream>
#include <map>
#include <optional>
#include <ostream>

#include "bucket.h"
#include "request.h"

// The vector of requests is required to be sorted by niceness and then time
// added such that lowest priority requests are at the end of the queue
static std::map<uint32_t, std::vector<scheduler::Request *>> request_queue = {};

bool compare_request_priority(const scheduler::Request *r1, const scheduler::Request *r2) {
    // TODO: Add secondary sort for time added if niceness are equal

    // Lower priority number is higher priority
    return r1->nice > r2->nice;
}

void scheduler::queue_request(scheduler::Request *request_) {
    std::vector<scheduler::Request *> &user_request_queue =
        request_queue.try_emplace(request_->user_id, std::vector<Request *>{}).first->second;

    auto sorting_iterator =
        std::lower_bound(user_request_queue.begin(), user_request_queue.end(), request_, compare_request_priority);
    user_request_queue.insert(sorting_iterator, request_);
}

void scheduler::queue_processing_work(const boost::system::error_code &error, boost::asio::steady_timer *queue_timer) {
    // TODO: Add mutex to containers used in this thread

    if (error) {
        std::cerr << "Error processing queue: " << error.what() << std::endl;
    }

    std::cout << "tick:: " << scheduler::requests_count() << std::endl;

    for (auto &[user_id, request_vector] : request_queue) {
        std::optional<size_t> requests_remaining = std::nullopt;

        std::cout << user_id << " :: " << request_vector.size() << std::endl;

        while (not requests_remaining.has_value() or requests_remaining > 0) {
            scheduler::Request *request_ = request_vector.front();
            requests_remaining = scheduler::try_immediate_insert_request(request_);
            request_vector.pop_back();
        }

        scheduler::recreate_bucket(user_id);
    }

    scheduler::decrement_niceness();

    queue_timer->expires_after(std::chrono::seconds(10));
    queue_timer->async_wait(
        boost::bind(scheduler::queue_processing_work, boost::asio::placeholders::error, queue_timer));
}
