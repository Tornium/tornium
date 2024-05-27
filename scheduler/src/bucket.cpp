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

#include "bucket.h"

#include <algorithm>
#include <iostream>
#include <map>
#include <ostream>

#include "http.h"
#include "request.h"
#include "request_queue.h"

// Mapping indicating relationship between a user and their request bucket
std::map<uint32_t, scheduler::RequestBucket> request_buckets = {};

scheduler::RequestBucket::RequestBucket() : start_timestamp(std::time(0)) {}
scheduler::insertion_status scheduler::RequestBucket::try_emplace(scheduler::Request *request_) {
    const bool has_maxed_requests = bucket_requests.size() > REQUESTS_PER_BUCKET;

    if (request_->request_type == nice_type::user_request or request_ -> request_type == nice_type::high_priority_request) {
        if (has_maxed_requests) {
            // If the bucket is full and the request is to be immediately inserted,
            // The lowest niceness request will be popped and added to the request
            // tree while this request is executed immediately

            std::sort(bucket_requests.begin(), bucket_requests.end(),
                      [](const scheduler::Request* first, const scheduler::Request* second) {
                return first->nice < second->nice;
            });

            if (bucket_requests.back()->request_type == nice_type::user_request) {
                // Don't need to check if vector is empty as it's already known that the
                // size is `max_requests`
                scheduler::Request *popped_request = bucket_requests.back();
                bucket_requests.pop_back();
                scheduler::queue_request(popped_request);
            }
        }

        bucket_requests.push_back(request_);
        return insertion_status::immediate_insert;
    }

    return insertion_status::queued;
}

scheduler::RequestBucket scheduler::insert_request(scheduler::Request *request_) {
    request_buckets.try_emplace(request_ -> user_id, scheduler::RequestBucket());
    scheduler::RequestBucket bucket_ = request_buckets[request_ -> user_id];  // TODO: Use the iterator from
                                                                           // try_emplace to get this
    switch (bucket_.try_emplace(request_)) {
        case scheduler::insertion_status::immediate_insert:
            scheduler::emplace_http_requeset(request_);

            // TODO: Remove request from wherever it's stored

            break;
        case scheduler::insertion_status::queued:
            scheduler::queue_request(request_);
            break;
        default:
            std::cerr << "Unknown scheduler insert status" << std::endl;
            abort();
    }

    return bucket_;
}
