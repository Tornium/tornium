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

#include "datagram_server.h"

#include <unistd.h>

#include <boost/asio/io_context.hpp>
#include <cstddef>
#include <iostream>

#include "bucket.h"
#include "config.h"
#include "request.h"

scheduler::DatagramServer::DatagramServer(boost::asio::io_context &io_context_, scheduler::config &config_)
    : socket_(io_context_, boost::asio::local::datagram_protocol::endpoint(config_.socket_path)){};

void scheduler::DatagramServer::do_receive() {
    socket_.async_receive_from(boost::asio::buffer(data_, SOCKET_BUFFER_MAX_LENGTH), sender_endpoint,
                               [this](boost::system::error_code error, std::size_t bytes_received) {
        if (error or bytes_received == 0) {
            do_receive();
            return;
        }

        std::optional<scheduler::Request *> r =
            scheduler::parse_request(data_, bytes_received, SOCKET_BUFFER_MAX_LENGTH);

        if (!r.has_value()) {
            do_receive();
            return;
        }

        if (scheduler::enqueue_request(r.value())) {
            // Request is not a pre-existing request that is linked to an existing request
            scheduler::insert_request(r.value());
        }

        do_receive();
    });
}
