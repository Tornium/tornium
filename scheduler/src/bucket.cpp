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

    if (request_->request_type == nice_type::user_request or
        request_->request_type == nice_type::high_priority_request) {
        if (has_maxed_requests) {
            // If the bucket is full and the request is to be immediately inserted,
            // The lowest niceness request will be popped and added to the request
            // queue while this request is executed immediately

            std::sort(bucket_requests.begin(), bucket_requests.end(),
                      [](const scheduler::Request *first, const scheduler::Request *second) {
                // Sorts the bucket's requests in ascending nice order
                // First request has the highest priority
                return first->nice < second->nice;
            });

            if (bucket_requests.back()->nice <= request_->nice) {
                // The priority of the lowest priority request in the bucket is greater
                // than that of the request that's to be inserted.
                // Therefore, the request that's to be inserted should just be queued.

                return insertion_status::queued;
            }

            // The lowest priority request in the bucket has a lower priority than this
            // request and can therefore be queued.
            scheduler::Request *popped_request = bucket_requests.back();
            bucket_requests.pop_back();
            scheduler::queue_request(popped_request);
        }

        bucket_requests.push_back(request_);
        return insertion_status::immediate_insert;
    }

    return insertion_status::queued;
}

scheduler::RequestBucket scheduler::insert_request(scheduler::Request *request_) {
    auto [bucket_, _] = request_buckets.try_emplace(request_->user_id, scheduler::RequestBucket());

    switch (bucket_->second.try_emplace(request_)) {
        case scheduler::insertion_status::immediate_insert:
            scheduler::emplace_http_requeset(request_);
            break;
        case scheduler::insertion_status::queued:
            scheduler::queue_request(request_);
            break;
        default:
            std::cerr << "Unknown scheduler insert status" << std::endl;
            abort();
    }

    return bucket_->second;
}
