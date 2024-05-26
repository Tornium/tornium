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
    DatagramServer(boost::asio::io_context& io_context, scheduler::config& config_);
    /**
     * @brief Wait for, read, parse, and handle datagram messages sent to the socket
     */
    void do_receive();

private:
    boost::asio::local::datagram_protocol::socket socket_;
    boost::asio::local::datagram_protocol::endpoint sender_endpoint;
    char data_[SOCKET_BUFFER_MAX_LENGTH];
    std::multimap<std::string, scheduler::Request&> requests_map {};

};
}

#endif
