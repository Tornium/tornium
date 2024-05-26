#include "datagram_server.h"
#include "bucket.h"
#include "config.h"
#include "request.h"
#include <boost/asio/io_context.hpp>
#include <cstddef>
#include <iostream>
#include <unistd.h>

scheduler::DatagramServer::DatagramServer(boost::asio::io_context& io_context_, scheduler::config& config_) : socket_(io_context_, boost::asio::local::datagram_protocol::endpoint(config_.socket_path)) {};

void scheduler::DatagramServer::do_receive() {
    // FIXME: Currenly will only process only request before it stops accepting messages
    socket_.async_receive_from(boost::asio::buffer(data_, SOCKET_BUFFER_MAX_LENGTH), sender_endpoint, [this](boost::system::error_code error, std::size_t bytes_received) {
        if (error or bytes_received == 0) {
            do_receive();
            return;
        }

        std::optional<scheduler::Request> r = scheduler::parse_request(data_, bytes_received, SOCKET_BUFFER_MAX_LENGTH);

        if (!r.has_value()) {
            do_receive();
            return;
        }

        if (scheduler::enqueue_request(requests_map, r.value())) {
            std::cout << "Received request... " << r -> endpoint_id << " :: " << (int) r -> nice << " :: " << r -> user_id << std::endl;
            scheduler::insert_request(r.value());
        } else {
            // TODO: Link request to pre-existing request
        }

        do_receive();
    });
}
