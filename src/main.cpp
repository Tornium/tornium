#include <boost/asio/buffer.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/ip/address.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/write.hpp>
#include <boost/beast/core/buffers_generator.hpp>
#include <boost/beast/core/error.hpp>
#include <boost/beast/core/flat_buffer.hpp>
#include <boost/beast/http/basic_dynamic_body.hpp>
#include <boost/beast/http/chunk_encode.hpp>
#include <boost/beast/http/dynamic_body.hpp>
#include <boost/beast/http/empty_body.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/http/serializer.hpp>
#include <boost/beast/http/status.hpp>
#include <boost/beast/http/string_body.hpp>
#include <boost/beast/http/write.hpp>
#include <boost/program_options.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <chrono>
#include <exception>
#include <fstream>
#include <iostream>
#include <optional>
#include <string>
#include <thread>

#include "client.h"

#ifndef GIT_COMMIT_HASH
#define GIT_COMMIT_HASH "?"
#endif

void temp_worker_task(int worker_id) { std::cout << "Worker #" << worker_id << " started" << std::endl; }

// Return a response for the given request.
template <class Body, class Allocator>
std::optional<boost::beast::http::message_generator> handle_request(
    boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
    boost::asio::ip::tcp::socket& socket_) {
    // Returns a bad request response
    auto const bad_request = [&req, &socket_](boost::beast::string_view why) {
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

    std::cout << req.method_string() << " " << req.target() << std::endl;

    // Make sure we can handle the method
    if (req.method() != boost::beast::http::verb::get && req.method() != boost::beast::http::verb::head) {
        return bad_request("Unknown HTTP-method");
    }

    // Request path must be absolute and not contain "..".
    if (req.target().empty() || req.target()[0] != '/' || req.target().find("..") != boost::beast::string_view::npos) {
        return bad_request("Illegal request-target");
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

    return std::nullopt;
}

int main(int argc, char* argv[]) {
    int worker_count = 1;
    int max_workers = 1;
    std::vector<std::thread> worker_threads;
    std::vector<sse_client::client> client_connections;

    try {
        std::string config_file;

        boost::program_options::options_description generic("Generic options");
        generic.add_options()("version,v", "Return version string")("help,h", "Return help message")(
            "config,c", boost::program_options::value<std::string>(&config_file)->default_value("sse-proxy.cfg"),
            "Path to configuration file")("print-config", "Print the configuration");

        boost::program_options::options_description config("Configuration");
        config.add_options()("workers", boost::program_options::value<int>(&worker_count), "Worker count");
        config.add_options()("max-workers", boost::program_options::value<int>(&max_workers), "Max worker count");

        boost::program_options::options_description cmdline_options;
        cmdline_options.add(generic).add(config);

        boost::program_options::options_description config_file_options;
        config_file_options.add(config);

        boost::program_options::variables_map vm;
        boost::program_options::store(
            boost::program_options::command_line_parser(argc, argv).options(cmdline_options).run(), vm);
        boost::program_options::notify(vm);

        std::ifstream ifs(config_file.c_str());
        if (!ifs) {
            std::cout << "can not open config file: " << config_file << "\n";
            return 1;
        } else {
            store(boost::program_options::parse_config_file(ifs, config_file_options), vm);
            notify(vm);
        }

        if (vm.count("help")) {
            std::cout << "Usage\n\tsse-proxy [options]\n" << cmdline_options << std::endl;
            return 0;
        } else if (vm.count("version")) {
            std::cout << "Tornium SSE-Proxy version 0.1.0-" << GIT_COMMIT_HASH << std::endl;
            return 0;
        } else if (vm.count("print-config")) {
            std::cout << "Workers: " << worker_count << "\n";
            return 0;
        }
    } catch (std::exception e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    for (int i = 0; i < worker_count; i++) {
        worker_threads.emplace_back(temp_worker_task, i);
    }

    // TODO: Create thread for socket reads

    for (std::thread& thread : worker_threads) {
        thread.join();
    }

    boost::asio::io_context ioc{1};
    boost::asio::ip::tcp::acceptor acceptor_{ioc, {boost::beast::net::ip::make_address("0.0.0.0"), 8081}};

    for (;;) {
        boost::asio::ip::tcp::socket socket_{ioc};
        acceptor_.accept(socket_);

        boost::beast::error_code ec;
        boost::beast::flat_buffer buffer;

        boost::beast::http::request<boost::beast::http::string_body> request_;
        boost::beast::http::read(socket_, buffer, request_, ec);

        if (ec == boost::beast::http::error::end_of_stream) {
            break;
        } else if (ec) {
            std::cerr << "HTTP read failed: " << ec.what() << std::endl;
            break;
        }

        // Handle request
        std::optional<boost::beast::http::message_generator> msg = handle_request(std::move(request_), socket_);

        // Send the response
        if (msg.has_value()) {
            boost::beast::write(socket_, msg.value(), ec);
            break;
        }

        if (ec) {
            std::cout << "Failed to write: " << ec.what() << std::endl;
            break;
        }

        for (int i = 0; i < 100; i++) {
            boost::asio::write(socket_, boost::asio::buffer("data: " + std::to_string(i) + "\n\n"), ec);
            if (ec) {
                std::cout << "Failed to write: " << ec.what() << std::endl;
                break;
            }
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }

        if (!ec) {
            sse_client::client client_{boost::uuids::to_string(boost::uuids::random_generator()()), std::move(socket_)};
            client_connections.push_back(std::move(client_));
        }
    }

    return 0;
}
