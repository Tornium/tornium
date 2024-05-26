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

#include "request.h"

#include <algorithm>
#include <boost/url.hpp>
#include <boost/url/parse.hpp>
#include <boost/url/parse_path.hpp>
#include <cstdio>
#include <iostream>
#include <map>
#include <optional>
#include <ostream>
#include <stdexcept>

static std::multimap<std::string, scheduler::Request &> requests_map = {};

std::optional<scheduler::Request> scheduler::parse_request(char *data_, const size_t &bytes_received,
                                                           const size_t &buffer_max_length) {
    uint8_t parse_step = 0;
    std::string nice_string = "";
    std::string endpoint = "";
    std::string user_string = "";
    std::string max_retries_string = "";

    for (size_t i = 0; i < std::min(bytes_received, buffer_max_length); i++) {
        if (data_[i] == '\n') {
            parse_step++;
            continue;
        }

        switch (parse_step) {
            case 0:
                nice_string += data_[i];
                break;
            case 1:
                endpoint += data_[i];
                break;
            case 2:
                user_string += data_[i];
                break;
            case 3:
                max_retries_string += data_[i];
                break;
        }
    }

    int8_t niceness;
    uint32_t user;
    uint8_t max_retries;
    scheduler::nice_type parsed_request_type;

    try {
        niceness = static_cast<int8_t>(std::stoi(nice_string));
        user = static_cast<uint32_t>(std::stoul(user_string));
        max_retries = static_cast<uint8_t>(std::stoi(max_retries_string));
    } catch (std::invalid_argument) {
        std::cerr << "Unable to parse request \"" << data_ << "\"... SKIPPING" << std::endl;
        return std::nullopt;
    }

    if (niceness <= -10) {
        parsed_request_type = scheduler::nice_type::user_request;
    } else if (niceness <= 0) {
        parsed_request_type = scheduler::nice_type::high_priority_request;
    } else {
        parsed_request_type = scheduler::nice_type::generic_request;
    }

    auto parsed_uri = boost::urls::parse_uri(endpoint);
    std::string endpoint_id = parsed_uri->path();

    if (parsed_uri->has_query()) {
        endpoint_id.append("?" + parsed_uri->query());
    }

    scheduler::Request request_ = {
        .nice = niceness,
        .endpoint = endpoint,
        .endpoint_id = endpoint_id,
        .user_id = user,
        .remaining_retries = max_retries,
        .linked_requests = std::vector<Request>{},
        .time_received = std::time(0),
        .time_scheduled = std::nullopt,
        .request_type = parsed_request_type,
    };

    return request_;
}

std::optional<scheduler::Request> scheduler::request_by_path(std::string path) {
    if (auto request_ = requests_map.find(path); request_ == requests_map.end()) {
        return std::nullopt;
    } else {
        return request_->second;
    }
}

bool scheduler::enqueue_request(scheduler::Request &request_) {
    // TODO: Rename function
    if (requests_map.count(request_.endpoint_id) > 0) {
        auto existing_keys_range = requests_map.equal_range(request_.endpoint_id);

        for (auto i = existing_keys_range.first; i != existing_keys_range.second; i++) {
            // TODO: Implement this to check the endpoint used to determine if the
            // request should be linked to the existing request
            return false;
        }
    }

    requests_map.insert({request_.endpoint_id, request_});
    return true;
}

bool scheduler::retry_request(scheduler::Request &request_) {
    if (request_.remaining_retries == 0) {
        return false;
    }

    request_.remaining_retries--;
    // TODO: Re-push request to the scheduler
    return true;
}

size_t scheduler::requests_count() { return requests_map.size(); }

void scheduler::remove_request(std::string request_key) { requests_map.erase(request_key); }

void scheduler::decrement_niceness() {
    // TODO: Rename function

    for (auto request_ : requests_map) {
        if (request_.second.time_scheduled != std::nullopt) {
            continue;
        }

        request_.second.nice--;
    }
}
