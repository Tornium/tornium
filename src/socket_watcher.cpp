#include "socket_watcher.h"

#include <algorithm>
#include <boost/asio.hpp>
#include <boost/asio/buffer.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/ip/address.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/placeholders.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/asio/write.hpp>
#include <boost/beast.hpp>
#include <boost/beast/core/buffers_generator.hpp>
#include <boost/beast/core/error.hpp>
#include <boost/beast/core/flat_buffer.hpp>
#include <boost/beast/http/basic_dynamic_body.hpp>
#include <boost/beast/http/chunk_encode.hpp>
#include <boost/beast/http/dynamic_body.hpp>
#include <boost/beast/http/empty_body.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/http/message_generator.hpp>
#include <boost/beast/http/serializer.hpp>
#include <boost/beast/http/status.hpp>
#include <boost/beast/http/string_body.hpp>
#include <boost/beast/http/write.hpp>
#include <boost/bind/bind.hpp>
#include <boost/program_options.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <chrono>
#include <iostream>
#include <string>
#include <vector>

void socket_watcher::socket_timer_callback(const boost::system::error_code& ec,
                                           std::map<std::string, boost::asio::ip::tcp::socket>* client_connections,
                                           boost::asio::steady_timer* socket_check_timer) {
    if (!ec) {
        std::vector<std::string> clients_to_close;

        for (auto iterator = client_connections->begin(); iterator != client_connections->end(); iterator++) {
            // uuid = iterator -> first
            // socket_ = iterator -> second
            boost::system::error_code write_ec;

            std::cout << "Checking client " << iterator->first << "\n";

            // TCP doesn't have a method to detect if a client has closed a connection without writing to the socket if
            // the socket isn't watching for FIN So this is writing to the socket with a ping event to determine if the
            // client and server are still connected
            boost::asio::write(iterator->second, boost::asio::buffer((std::string) "event: ping" + "\n\n"), write_ec);

            // FIXME: Socket isn't closed and removed on the first write after the socket is (assumed to be) closed

            if (!write_ec) {
                continue;
            }

            std::cout << "Socket to client " << iterator->first << " has been closed by the client: " << write_ec.what()
                      << "\n";
            iterator->second.close();
            clients_to_close.emplace_back(iterator->first);
        }

        std::for_each(clients_to_close.begin(), clients_to_close.end(),
                      [&client_connections](const std::string client_uuid) {
            std::cout << "Removing client connection for " << client_uuid << "\n";
            client_connections->erase(client_uuid);
        });
    } else {
        std::cout << "Socket check timer failed: " << ec.what() << std::endl;
    }

    socket_check_timer->expires_after(std::chrono::minutes(1));
    socket_check_timer->async_wait(
        boost::bind(socket_timer_callback, boost::asio::placeholders::error, client_connections, socket_check_timer));
}

void socket_watcher::start_unix_socket_worker(std::map<std::string, boost::asio::ip::tcp::socket>& client_connections,
                                              boost::asio::io_context& ioc) {
    std::cout << "Unix socket worker started" << std::endl;
    boost::asio::steady_timer socket_check_timer(ioc, std::chrono::minutes(1));
    socket_check_timer.async_wait(boost::bind(socket_watcher::socket_timer_callback, boost::asio::placeholders::error,
                                              &client_connections, &socket_check_timer));
    ioc.run();
}
