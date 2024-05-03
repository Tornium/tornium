#include <boost/asio/io_context.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/beast.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <ctime>

namespace sse_client {

class client {
   public:
    explicit client(const std::string client_id, const boost::asio::ip::tcp::socket& socket_);

   private:
    std::string client_id;
    const boost::asio::ip::tcp::socket& socket_;
};
}  // namespace sse_client
