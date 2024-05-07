#include "http.h"

#include <bits/types/time_t.h>

#include <boost/beast.hpp>
#include <boost/smart_ptr/make_shared_array.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <ctime>
#include <optional>
#include <pqxx/pqxx>

#include "client.h"

template <class Body, class Allocator>
client::client http::handle_request(
    boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
    boost::asio::ip::tcp::socket& socket_, pqxx::connection& connection_) {
    // Returns a bad request response
    auto const bad_request = [&req](boost::beast::string_view why) {
        boost::beast::http::response<boost::beast::http::string_body> res{boost::beast::http::status::bad_request,
                                                                          req.version()};
        res.set(boost::beast::http::field::server, BOOST_BEAST_VERSION_STRING);
        res.set(boost::beast::http::field::content_type, "text/html");
        res.keep_alive(req.keep_alive());
        res.body() = std::string(why);
        res.prepare_payload();
        return res;
    };

    // Returns a not found response
    auto const not_found = [&req](boost::beast::string_view target) {
        boost::beast::http::response<boost::beast::http::string_body> res{boost::beast::http::status::not_found,
                                                                          req.version()};
        res.set(boost::beast::http::field::server, BOOST_BEAST_VERSION_STRING);
        res.set(boost::beast::http::field::content_type, "text/html");
        res.keep_alive(req.keep_alive());
        res.body() = "The resource '" + std::string(target) + "' was not found.";
        res.prepare_payload();
        return res;
    };

    // Returns a server error response
    auto const server_error = [&req](boost::beast::string_view what) {
        boost::beast::http::response<boost::beast::http::string_body> res{
            boost::beast::http::status::internal_server_error, req.version()};
        res.set(boost::beast::http::field::server, BOOST_BEAST_VERSION_STRING);
        res.set(boost::beast::http::field::content_type, "text/html");
        res.keep_alive(req.keep_alive());
        res.body() = "An error occurred: '" + std::string(what) + "'";
        res.prepare_payload();
        return res;
    };

    // Make sure we can handle the method
    if (req.method() != boost::beast::http::verb::get && req.method() != boost::beast::http::verb::head) {
        return {bad_request("Unknown HTTP-method"), std::nullopt, std::nullopt};
    }

    // Request path must be absolute and not contain "..".
    if (req.target().empty() || req.target()[0] != '/' || req.target().find("..") != boost::beast::string_view::npos) {
        return {bad_request("Illegal request-target"), std::nullopt, std::nullopt};
    } else if (req.target() == "/") {
        return {bad_request("Client ID required"), std::nullopt, std::nullopt};
    }

    std::string client_id = req.target().substr(1);

    if (client_id.length() != 32) {
        return {bad_request("Invalid client ID (length)"), std::nullopt, std::nullopt};
    }

    pqxx::work transaction(connection_);
    pqxx::row client_row;

    try {
        client_row = transaction.exec_params1(
            "SELECT user_id, time_created, revoked_in FROM gatewayclient WHERE client_id = $1", client_id);
    } catch (std::exception) {
        return {bad_request("Invalid client ID"), std::nullopt};
    }

    std::tm time_created_tm;
    strptime(client_row["time_created"].as<std::string>().c_str(), "%Y-%m-%d %H:%M:%S", &time_created_tm);
    time_t time_created = mktime(&time_created_tm);

    if (time_created + client_row["revoked_in"].as<int>() < std::time(nullptr)) {
        return {bad_request("Client expired"), std::nullopt, std::nullopt};
    }

    // Respond to GET request
    boost::beast::http::response<boost::beast::http::empty_body> res;
    res.result(boost::beast::http::status::ok);
    res.set(boost::beast::http::field::server, BOOST_BEAST_VERSION_STRING);
    res.set(boost::beast::http::field::content_type, "text/event-stream; charset=utf-8");
    res.set(boost::beast::http::field::cache_control, "no-cache");
    res.set("Access-Control-Allow-Origin", "*");
    res.set("Access-Control-Allow-Credentials", "true");
    res.set("X-Accel-Buffering", "no");
    res.keep_alive(true);

    boost::beast::http::response_serializer<boost::beast::http::empty_body> sr{res};
    boost::beast::http::write_header(socket_, sr);

    return {std::nullopt, client_id, client_row["user_id"].as<int>()};
}
