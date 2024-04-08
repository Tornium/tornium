#include "shard.h"

#include <boost/asio.hpp>
#include <boost/asio/buffer.hpp>
#include <boost/asio/buffers_iterator.hpp>
#include <boost/asio/registered_buffer.hpp>
#include <boost/asio/ssl.hpp>
#include <boost/beast/core/bind_handler.hpp>
#include <boost/beast/core/buffers_prefix.hpp>
#include <boost/beast/core/error.hpp>
#include <iostream>
#include <nlohmann/json.hpp>
#include <string>

using namespace nlohmann;

void fail(boost::beast::error_code ec, char const *what) { std::cerr << what << ": " << ec.message() << "\n"; }

namespace ws_shard {
shard::shard(boost::asio::io_context &io_context, boost::asio::ssl::context &ctx, size_t &shard_id, size_t &shard_count,
             std::string &discord_token, std::string &gateway_url)
    : resolver_(boost::asio::make_strand(io_context)),
      ws_(boost::asio::make_strand(io_context), ctx),
      shard_id(shard_id),
      shard_count(shard_count),
      discord_token(discord_token),
      gateway_url(gateway_url) {}

void shard::run(boost::asio::ip::tcp::resolver::results_type &resolved_gateway) {
    // Set a timeout on the operation
    boost::beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));

    // Make the connection on the IP address we get from a lookup
    boost::beast::get_lowest_layer(ws_).async_connect(
        resolved_gateway, boost::beast::bind_front_handler(&shard::on_connect, shared_from_this()));
}

void shard::on_connect(boost::beast::error_code error_code,
                       boost::asio::ip::tcp::resolver::results_type::endpoint_type endpoint_type) {
    if (error_code) {
        return fail(error_code, "connect");
    }

    boost::beast::get_lowest_layer(ws_).expires_after(std::chrono::seconds(30));

    // Set SNI Hostname (many hosts need this to handshake successfully)
    if (!SSL_set_tlsext_host_name(ws_.next_layer().native_handle(), gateway_url.substr(6).c_str())) {
        error_code =
            boost::beast::error_code(static_cast<int>(::ERR_get_error()), boost::asio::error::get_ssl_category());
        return fail(error_code, "connect");
    }

    ws_.next_layer().async_handshake(boost::asio::ssl::stream_base::client,
                                     boost::beast::bind_front_handler(&shard::on_ssl_handshake, shared_from_this()));
}

void shard::on_ssl_handshake(boost::beast::error_code error_code) {
    if (error_code) {
        return fail(error_code, "ssl_handshake");
    }

    // Turn off the timeout on the tcp_stream, because
    // the websocket stream has its own timeout system.
    boost::beast::get_lowest_layer(ws_).expires_never();

    // Set suggested timeout settings for the websocket
    ws_.set_option(boost::beast::websocket::stream_base::timeout::suggested(boost::beast::role_type::client));

    // Set a decorator to change the User-Agent of the handshake
    ws_.set_option(boost::beast::websocket::stream_base::decorator([](boost::beast::websocket::request_type &req) {
        req.set(boost::beast::http::field::user_agent,
                std::string(BOOST_BEAST_VERSION_STRING) + " websocket-client-async-ssl");
    }));

    // Perform the websocket handshake
    ws_.async_handshake(gateway_url.substr(6) + ":443", "/?v=10&encoding=json",
                        boost::beast::bind_front_handler(&shard::on_handshake, shared_from_this()));
}

void shard::on_handshake(boost::beast::error_code error_code) {
    if (error_code) {
        return fail(error_code, "handshake");
    }

    ws_.async_read(buffer_, boost::beast::bind_front_handler(&shard::on_hello, shared_from_this()));
}

void shard::on_hello(boost::beast::error_code error_code, size_t bytes_transferred) {
    if (error_code) {
        return fail(error_code, "handshake");
    }

    const auto parsed_op_response =
        json::parse(boost::asio::buffers_begin(buffer_.data()), boost::asio::buffers_end(buffer_.data()));

    if (not parsed_op_response.contains("op") or parsed_op_response["op"] != 10) {
        std::cerr << "Invalid OP response on heartbeat" << std::endl;
        std::cerr << parsed_op_response << std::endl;
        return;
    }

    heartbeat_interval = parsed_op_response["d"]["heartbeat_interval"];
    std::cout << "Setting hardbeat of shard ID " << shard_id << " to " << heartbeat_interval << " milliseconds"
              << std::endl;

    shard::send_heartbeat();
    // TODO: Start heartbeat timer

    // TODO: Send identity OP
    shard::send_ident();

    // TODO: Receive ready OP
}

void shard::send_heartbeat() {
    if (last_sequence.has_value()) {
        ws_.write(boost::asio::buffer("{'op': 1, 'd': " + std::to_string(last_sequence.value()) + "}"));
    } else {
        ws_.write(boost::asio::buffer("{'op': 1, 'd': null}"));
    }
}

void shard::send_ident() {
    // Intents include:
    //  - READY
    //  - RESUMED
    //  - VOICE_SERVER_UPDATE
    //  - USER_UPDATE
    //  - INTERACTION_CREATE
    //  - GUILD_MEMBER_ADD
    //  - GUILD_MEMBER_UPDATE
    //  - GUILD_MEMBER_REMOVE
    //  - THREAD_MEMBERS_UPDATE
    ws_.write(boost::asio::buffer("{'op': 2, 'd': {'token': '" + discord_token +
                                  "', 'intents': 2, 'properties': {'os': 'linux', 'browser': 'dateway', "
                                  "'device': 'dateway'}, 'shard': [" +
                                  std::to_string(shard_id) + ", " + std::to_string(shard_count) + "]}"));
}
}  // namespace ws_shard
