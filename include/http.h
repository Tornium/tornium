#include <boost/beast.hpp>
#include <optional>

namespace http {
template <class Body, class Allocator>
std::optional<boost::beast::http::message_generator> handle_request(
    boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
    boost::asio::ip::tcp::socket& socket_);
}
