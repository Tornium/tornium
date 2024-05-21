#ifndef SOCKET_WATCHER_H
#define SOCKET_WATCHER_H

#include <boost/asio.hpp>
#include <boost/system.hpp>
#include <map>

namespace socket_watcher {
void socket_timer_callback(const boost::system::error_code& ec,
                           std::map<std::string, boost::asio::ip::tcp::socket>* client_connections,
                           boost::asio::steady_timer* socket_check_timer);

void start_unix_socket_worker(std::map<std::string, boost::asio::ip::tcp::socket>& client_connections,
                              boost::asio::io_context& ioc);
}  // namespace socket_watcher

#endif
