#ifndef CLIENT_H
#define CLIENT_H

#include <boost/beast.hpp>
#include <optional>
#include <pqxx/pqxx>
#include <string>

namespace client {
struct client {
    std::optional<boost::beast::http::message_generator> msg;
    std::optional<std::string> client_id;
    std::optional<int> user_id;
};
}  // namespace client

#endif
