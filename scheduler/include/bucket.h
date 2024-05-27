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

#ifndef BUCKET_H
#define BUCKET_H

#include "request.h"

#define REQUESTS_PER_BUCKET 6
#define BUCKET_INTERVAL 10

namespace scheduler {
enum class insertion_status { queued, immediate_insert };

class RequestBucket {
   public:
    RequestBucket();
    insertion_status try_emplace(scheduler::Request *request_);

   private:
    const std::time_t start_timestamp;
    std::vector<scheduler::Request*> bucket_requests;
};

/**
 * @brief Insert request into a bucket and perform actions depending on priority
 *
 * @param request_ The request being made
 * @return Bucket the request is inserted into
 */
scheduler::RequestBucket insert_request(scheduler::Request *request_);
}  // namespace scheduler

#endif
