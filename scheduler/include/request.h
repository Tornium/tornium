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

#ifndef REQUEST_H
#define REQUEST_H

#include <cstdint>
#include <ctime>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace scheduler {
enum class nice_type { user_request, high_priority_request, generic_request };

struct Request {
    int8_t nice;
    std::string endpoint;
    std::string endpoint_id;
    uint32_t user_id;
    uint8_t remaining_retries;

    std::vector<Request> linked_requests;

    std::time_t time_received;
    std::optional<std::time_t> time_scheduled;
    nice_type request_type;
};

std::optional<Request> parse_request(char *data_, const size_t &bytes_received, const size_t &buffer_max_length);
std::optional<Request> request_by_path(std::string path);

/**
 * @brief Try to insert the request into the list of all received requests that
 * haven't been completed
 *
 * @param request_ Reference to the request received
 * @return True if the request has been added to the multimap, False if the
 * request wasn't able to be added and needs to be linked to an existing request
 */
bool enqueue_request(Request &request_);
bool retry_request(Request &request_);

size_t requests_count();
void remove_request(std::string request_key);
void decrement_niceness();
}  // namespace scheduler

#endif
