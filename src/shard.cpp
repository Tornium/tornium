#include "shard.h"

#include <unistd.h>

#include <boost/asio.hpp>
#include <boost/asio/buffer.hpp>
#include <boost/asio/buffers_iterator.hpp>
#include <boost/asio/detail/chrono.hpp>
#include <boost/asio/registered_buffer.hpp>
#include <boost/asio/ssl.hpp>
#include <boost/asio/strand.hpp>
#include <boost/beast/core/bind_handler.hpp>
#include <boost/beast/core/buffers_prefix.hpp>
#include <boost/beast/core/error.hpp>
#include <boost/beast/core/flat_buffer.hpp>
#include <boost/beast/core/make_printable.hpp>
#include <boost/beast/core/stream_traits.hpp>
#include <boost/beast/websocket/rfc6455.hpp>
#include <boost/bind.hpp>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include <iostream>
#include <nlohmann/json.hpp>
#include <optional>
#include <string>

#include "celery.h"

using namespace nlohmann;

void fail(boost::beast::error_code ec, char const *what) { std::cerr << what << ": " << ec.message() << "\n"; }

namespace ws_shard {
shard::shard(boost::asio::io_context &io_context_, boost::asio::ssl::context &ctx_, size_t &shard_id_,
             size_t &shard_count_, std::string &discord_token_, std::string &gateway_url_)
    : resolver_(boost::asio::make_strand(io_context_)),
      ioc(io_context_),
      shard_id(shard_id_),
      shard_count(shard_count_),
      discord_token(discord_token_),
      gateway_url(gateway_url_),
      ssl_ctx(ctx_),
      heartbeat_timer(io_context_, boost::asio::chrono::milliseconds(30000)) {
    ws_.emplace(boost::asio::make_strand(io_context_), ctx_);
}

void shard::run(boost::asio::ip::tcp::resolver::results_type &resolved_gateway) {
    if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    // Set a timeout on the operation
    boost::beast::get_lowest_layer(ws_.value()).expires_after(std::chrono::seconds(30));

    // Make the connection on the IP address we get from a lookup
    boost::beast::get_lowest_layer(ws_.value())
        .async_connect(resolved_gateway, boost::beast::bind_front_handler(&shard::on_connect, shared_from_this()));
}

void shard::on_connect(boost::beast::error_code error_code,
                       boost::asio::ip::tcp::resolver::results_type::endpoint_type) {
    if (error_code) {
        return fail(error_code, "connect");
    } else if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    if (status != shard_status::reconnecting) {
        status = shard_status::connecting;
    }

    boost::beast::get_lowest_layer(ws_.value()).expires_after(std::chrono::seconds(30));

    // Set SNI Hostname (many hosts need this to handshake successfully)
    if (!SSL_set_tlsext_host_name(ws_.value().next_layer().native_handle(), gateway_url.substr(6).c_str())) {
        error_code =
            boost::beast::error_code(static_cast<int>(::ERR_get_error()), boost::asio::error::get_ssl_category());
        return fail(error_code, "connect");
    }

    ws_.value().next_layer().async_handshake(
        boost::asio::ssl::stream_base::client,
        boost::beast::bind_front_handler(&shard::on_ssl_handshake, shared_from_this()));
}

void shard::on_ssl_handshake(boost::beast::error_code error_code) {
    if (error_code) {
        return fail(error_code, "ssl_handshake");
    } else if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    if (status != shard_status::reconnecting) {
        status = shard_status::connecting;
    }

    // Turn off the timeout on the tcp_stream, because
    // the websocket stream has its own timeout system.
    boost::beast::get_lowest_layer(ws_.value()).expires_never();

    // Set suggested timeout settings for the websocket
    ws_.value().set_option(boost::beast::websocket::stream_base::timeout::suggested(boost::beast::role_type::client));

    // Set a decorator to change the User-Agent of the handshake
    ws_.value().set_option(
        boost::beast::websocket::stream_base::decorator([](boost::beast::websocket::request_type &req) {
        req.set(boost::beast::http::field::user_agent,
                std::string(BOOST_BEAST_VERSION_STRING) + " Boost Beast (Tornium Dateway)");
    }));

    // Perform the websocket handshake
    ws_.value().async_handshake(gateway_url.substr(6) + ":443", "/?v=10&encoding=json",
                                boost::beast::bind_front_handler(&shard::on_handshake, shared_from_this()));
}

void shard::on_handshake(boost::beast::error_code error_code) {
    if (error_code) {
        return fail(error_code, "handshake");
    }

    if (status == shard_status::reconnecting) {
        ws_.value().async_read(buffer_, boost::beast::bind_front_handler(&shard::on_reconnect, shared_from_this()));
    } else {
        ws_.value().async_read(buffer_, boost::beast::bind_front_handler(&shard::on_hello, shared_from_this()));
    }

    status = shard_status::connecting;
}

void shard::on_hello(boost::beast::error_code error_code, size_t bytes_transferred) {
    if (error_code) {
        return fail(error_code, "handshake");
    } else if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    const auto parsed_op_response =
        json::parse(boost::asio::buffers_begin(buffer_.data()), boost::asio::buffers_end(buffer_.data()));
    buffer_.consume(bytes_transferred);

    if (not parsed_op_response.contains("op") or parsed_op_response["op"] != 10) {
        std::cerr << "Invalid OP response on heartbeat" << std::endl;
        std::cerr << parsed_op_response << std::endl;

        // TODO: Send disconnect OP
        status = shard_status::disconnected;
        return;
    }

    heartbeat_interval = parsed_op_response["d"]["heartbeat_interval"];
    std::cout << "Setting hardbeat of shard ID " << shard_id << " to " << heartbeat_interval << " milliseconds"
              << std::endl;

    // Send heartbeat op and start timer for heartbeats
    // TODO: Set heartbeat interval in existing timer to prevent gateway close
    shard::send_heartbeat();
    heartbeat_timer.async_wait(boost::bind(&shard::heartbeat, this));

    // Send identity op
    shard::send_ident();
    std::cout << "Ident sent" << std::endl;

    status = shard_status::ready;

    // Read ready op
    ws_.value().async_read(buffer_, boost::beast::bind_front_handler(&shard::on_read, shared_from_this()));
}

void shard::on_reconnect(boost::beast::error_code error_code, size_t bytes_transferred) {
    if (error_code) {
        return fail(error_code, "handshake");
    } else if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    // TODO: Check sequence and session ID for existence

    const auto parsed_op_response =
        json::parse(boost::asio::buffers_begin(buffer_.data()), boost::asio::buffers_end(buffer_.data()));
    buffer_.consume(bytes_transferred);

    if (not parsed_op_response.contains("op") or parsed_op_response["op"] != 10) {
        std::cerr << "Invalid OP response on heartbeat" << std::endl;
        std::cerr << parsed_op_response << std::endl;

        // TODO: Send disconnect OP
        status = shard_status::disconnected;
        return;
    }

    heartbeat_interval = parsed_op_response["d"]["heartbeat_interval"];
    std::cout << "Setting hardbeat of shard ID " << shard_id << " to " << heartbeat_interval << " milliseconds"
              << std::endl;

    status = shard_status::ready;

    json resume_op{
        {"op", 6},
        {"d", {{"token", discord_token}, {"session_id", session_id.value()}, {"seq", last_sequence.value()}}}};
    ws_->async_write(boost::asio::buffer(resume_op.dump()),
                     boost::beast::bind_front_handler(&shard::on_read, shared_from_this()));
}

void shard::send_heartbeat() {
    json heartbeat_op{{"op", 1}};

    if (last_sequence.has_value()) {
        heartbeat_op["d"] = last_sequence.value();
    } else {
        heartbeat_op["d"] = "null";
    }

    // ws_ -> async_write(boost::asio::buffer(heartbeat_op.dump()), boost::beast::bind_front_handler(&shard::on_read,
    // shared_from_this()));
    ws_->async_write(boost::asio::buffer(heartbeat_op.dump()), [&](boost::beast::error_code, size_t) {});
    std::cout << std::time(0) << " :: Heartbeat sent" << std::endl;
}

void shard::heartbeat() {
    if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    if (last_heartbeat.has_value() and
        std::difftime(std::time(0), last_heartbeat.value()) > static_cast<double>(heartbeat_interval / 1000)) {
        // Gateway hasn't responded to the heartbeat, indicating a failed/zombied connection
        // Connection should be terminated with a close code other than 1000 and 1001
        // Then attempt to resume the connection

        std::cout << std::time(0) << " :: Missing heartbeat" << std::endl;
        status = shard_status::disconnected;

        json reconnect_op{{"op", 4000}};
        ws_->async_write(boost::asio::buffer(reconnect_op.dump()),
                         boost::beast::bind_front_handler(&shard::on_read, shared_from_this()));

        status = shard_status::reconnecting;

        shard::reconnect();
        return;
    }

    try {
        shard::send_heartbeat();
    } catch (boost::system::system_error e) {
        status = shard_status::disconnected;
        std::cout << std::time(0) << " :: Failed to send heartbeat due to " << e.what() << " ... reconnecting"
                  << std::endl;
        shard::reconnect();
    }

    heartbeat_timer.expires_at(
        heartbeat_timer.expires_at() +
        boost::asio::chrono::milliseconds((size_t)((float)(std::rand()) * heartbeat_interval / (float)(RAND_MAX))));
    heartbeat_timer.async_wait(boost::bind(&shard::heartbeat, this));
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
    json hello_op{
        {"op", 2},
        {"d",
         {{"token", discord_token},
          {"intents", 2},
          {"properties", {{"os", "linux"}, {"browser", "Tornium (dateway)"}, {"device", "Tornium (dateway)"}}},
          {"shard", {shard_id, shard_count}}}}};
    ws_.value().write(boost::asio::buffer(hello_op.dump(4)));
}

void shard::on_read(boost::beast::error_code error_code, size_t bytes_transferred) {
    if (error_code) {
        fail(error_code, "read");
        shard::reconnect();
        return;
        // } else if (status != shard_status::ready) {
        //     std::cerr << "Shard ID " << shard_id << " is not ready. Blocking reads." << std::endl;
        //     return;
    } else if (!ws_.has_value()) {
        shard::reconnect();
        return;
    }

    json parsed_buffer;

    try {
        parsed_buffer =
            json::parse(boost::asio::buffers_begin(buffer_.data()), boost::asio::buffers_end(buffer_.data()));
    } catch (json::parse_error e) {
        std::cerr << "Failed to parse buffer of " << bytes_transferred << " bytes" << std::endl;
        std::cerr << e.what() << std::endl;
        std::cout << boost::beast::make_printable(buffer_.data()) << std::endl;
        buffer_.clear();

        ws_.value().async_read(buffer_, boost::beast::bind_front_handler(&shard::on_read, shared_from_this()));
        return;
    }

    std::cout << boost::beast::make_printable(buffer_.data()) << std::endl;
    buffer_.clear();

    // Store the last sequence number if one exists
    // https://discord.com/developers/docs/topics/gateway#heartbeat-interval
    if (not parsed_buffer.contains("s") or parsed_buffer["s"].is_null()) {
        last_sequence = std::nullopt;
    } else if (parsed_buffer.contains("s") and not parsed_buffer["s"].is_null()) {
        last_sequence = parsed_buffer["s"];
    }

    if (parsed_buffer["op"] == 11) {
        // Heartbeat ACK
        last_heartbeat = std::time(0);
    } else if (parsed_buffer["op"] == 7) {
        // Reconnect (op 7)
        // https://discord.com/developers/docs/topics/gateway#resuming
        shard::reconnect();
        return;
    } else if (parsed_buffer["op"] == 9 and parsed_buffer["d"] == false) {
        // Invalid session (op 9)
        // Upon an attempted reconnect, the session was too old and will need to be reconnected from scratch
        // https://discord.com/developers/docs/topics/gateway#resuming
        // https://discord.com/developers/docs/topics/gateway-events#invalid-session

        shard::reconnect();
        return;
    } else if (parsed_buffer["op"] == 9 and parsed_buffer["d"] == true) {
        // Invalid session (op 9)
        // Unlikely event, but client should resume the connection
        // https://discord.com/developers/docs/topics/gateway#resuming
        // https://discord.com/developers/docs/topics/gateway-events#invalid-session

        shard::reconnect();
        return;
    } else if (parsed_buffer["op"] == 0 and parsed_buffer["t"] == "READY") {
        // Gateway ready to interact with this client
        // https://discord.com/developers/docs/topics/gateway#ready-event

        // Update data for resume op
        gateway_url = parsed_buffer["d"]["resume_gateway_url"];
        session_id = parsed_buffer["d"]["session_id"];

        std::cout << "Shard ID " << shard_id << " is ready" << std::endl;
        std::cout << "Setting gateway URL of shard ID " << shard_id << " to " << gateway_url << std::endl;
    } else if (parsed_buffer["op"] == 0 and parsed_buffer["t"] == "GUILD_MEMBER_ADD") {
        // Discord user joined server
        // {"t":"GUILD_MEMBER_ADD","s":2,"op":0,"d":{"user":{"username":"tiksantesting","public_flags":0,"id":"760910136960745493","global_name":null,"discriminator":"0","avatar_decoration_data":null,"avatar":"b4f5107be04841665055788f029ab7f5"},"unusual_dm_activity_until":null,"roles":[],"premium_since":null,"pending":false,"nick":null,"mute":false,"joined_at":"2024-04-09T04:00:26.288963+00:00","guild_id":"1132079436691415120","flags":0,"deaf":false,"communication_disabled_until":null,"avatar":null}}

        uint64_t user_discord_id = (uint64_t)std::stoll((std::string)parsed_buffer["d"]["user"]["id"]);
        std::cout << "Discord user ID " << user_discord_id << " joined server" << std::endl;
        celery::send_guild_member_add(parsed_buffer);
    } else if (parsed_buffer["op"] == 0 and parsed_buffer["t"] == "RESUMED") {
        // Connection to gateway has been resumed after a opcode 6 was sent
        // https://discord.com/developers/docs/topics/gateway-events#resumed
    }

    ws_->async_read(buffer_, boost::beast::bind_front_handler(&shard::on_read, shared_from_this()));
}

void shard::reconnect() {
    // Reconnect to the gateway
    // https://discord.com/developers/docs/topics/gateway#resuming

    if (status != shard_status::ready) {
        return;
    }

    status = shard_status::reconnecting;
    std::cout << "Shard ID " << shard_id << " reconnecting to gateway" << std::endl;

    // Make sure that the heartbeat timer doesn't attempt to perform a heartbeat op while reconnecting to the gateway
    heartbeat_timer.cancel();

    // Make sure that the read buffer is empty
    buffer_.clear();

    if (ws_->is_open()) {
        ws_->close(boost::beast::websocket::close_code::normal);
    }

    ws_.emplace(ioc, ssl_ctx);

    boost::asio::ip::tcp::resolver::results_type resolved_gateway;

    try {
        resolved_gateway = resolver_.resolve((std::string)gateway_url.substr(6), "443");
    } catch (std::exception e) {
        std::cerr << "Failed to resolve " << gateway_url << std::endl;
        std::cerr << e.what() << std::endl;

        status = shard_status::disconnected;
        return;
    }

    run(resolved_gateway);
}
}  // namespace ws_shard
