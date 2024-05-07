#ifndef HTTP_H
#define HTTP_H

#include <boost/beast.hpp>
#include <optional>
#include <pqxx/pqxx>

namespace http {
template <class Body, class Allocator>
std::tuple<std::optional<boost::beast::http::message_generator>, std::optional<std::string>> handle_request(
    boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
    boost::asio::ip::tcp::socket& socket_, pqxx::connection& c);
}

#endif
