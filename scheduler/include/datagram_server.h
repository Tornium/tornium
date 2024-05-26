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

#ifndef DATAGRAM_SERVER_H
#define DATAGRAM_SERVER_H

#include "config.h"
#include "request.h"
#include <boost/asio.hpp>
#include <boost/asio/io_context.hpp>
#include <map>

#define SOCKET_BUFFER_MAX_LENGTH 128

namespace scheduler {
class DatagramServer {
public:
  DatagramServer(boost::asio::io_context &io_context,
                 scheduler::config &config_);
  /**
   * @brief Wait for, read, parse, and handle datagram messages sent to the
   * socket
   */
  void do_receive();

private:
  boost::asio::local::datagram_protocol::socket socket_;
  boost::asio::local::datagram_protocol::endpoint sender_endpoint;
  char data_[SOCKET_BUFFER_MAX_LENGTH];
  std::multimap<std::string, scheduler::Request &> requests_map{};
};
} // namespace scheduler

#endif
