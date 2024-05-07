#ifndef HTTP_H
#define HTTP_H

#include <boost/beast.hpp>
#include <pqxx/pqxx>

#include "client.h"

namespace http {
template <class Body, class Allocator>
client::client handle_request(boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
                              boost::asio::ip::tcp::socket& socket_, pqxx::connection& c);
}

#endif
