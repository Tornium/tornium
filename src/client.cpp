#include "client.h"

#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid_io.hpp>

namespace sse_client {
client::client(std::string client_id, const boost::asio::ip::tcp::socket& socket_)
    : client_id(client_id), socket_(socket_){};
}
