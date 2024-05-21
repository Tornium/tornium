#include <boost/asio/io_context.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/beast.hpp>
#include <boost/beast/ssl.hpp>
#include <boost/beast/websocket.hpp>
#include <ctime>
#include <optional>

namespace ws_shard {
enum class shard_status { not_started, connecting, ready, disconnected, reconnecting };

class shard : public std::enable_shared_from_this<shard> {
    boost::asio::ip::tcp::resolver resolver_;
    std::optional<boost::beast::websocket::stream<boost::beast::ssl_stream<boost::beast::tcp_stream>>> ws_;
    boost::beast::flat_buffer buffer_;
    boost::asio::io_context &ioc;

    const size_t shard_id;
    const size_t &shard_count;
    const std::string &discord_token;
    shard_status status = shard_status::not_started;

    std::string gateway_url;
    std::optional<std::string> session_id = std::nullopt;
    boost::asio::ssl::context &ssl_ctx;

    size_t heartbeat_interval;
    std::optional<size_t> last_sequence = std::nullopt;
    std::optional<std::time_t> last_heartbeat = std::nullopt;
    boost::asio::steady_timer heartbeat_timer;

   public:
    explicit shard(boost::asio::io_context &io_context, boost::asio::ssl::context &ctx, size_t &shard_id,
                   size_t &shard_count, std::string &discord_token, std::string &gateway_url);
    void run(boost::asio::ip::tcp::resolver::results_type &resolved_gateway);
    void on_resolve(boost::beast::error_code error_code, boost::asio::ip::tcp::resolver::results_type results);
    void on_connect(boost::beast::error_code error_code,
                    boost::asio::ip::tcp::resolver::results_type::endpoint_type endpoint_type);
    void on_ssl_handshake(boost::beast::error_code error_code);
    void on_handshake(boost::beast::error_code error_code);
    void on_write(boost::beast::error_code error_code, size_t bytes_transferred);
    void on_read(boost::beast::error_code error_code, size_t bytes_transferred);
    void on_hello(boost::beast::error_code error_code, size_t bytes_transferred);
    void on_reconnect(boost::beast::error_code error_code, size_t bytes_transferred);
    void send_heartbeat();
    void heartbeat();
    void send_ident();
    void on_close(boost::beast::error_code error_code);
    void reconnect();

   private:
};
}  // namespace ws_shard
