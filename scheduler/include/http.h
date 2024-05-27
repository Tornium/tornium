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

#ifndef HTTP_H
#define HTTP_H

#include "request.h"

namespace scheduler {
void emplace_http_requeset(scheduler::Request *request_);
void start_curl_uv_loop();

struct http_response {
    char *response_body;
};
}  // namespace scheduler

#endif
