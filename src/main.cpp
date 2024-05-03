#include <algorithm>
#include <boost/asio.hpp>
#include <boost/asio/buffer.hpp>
#include <boost/asio/io_context.hpp>
#include <boost/asio/ip/address.hpp>
#include <boost/asio/ip/tcp.hpp>
#include <boost/asio/placeholders.hpp>
#include <boost/asio/steady_timer.hpp>
#include <boost/asio/write.hpp>
#include <boost/beast.hpp>
#include <boost/beast/core/buffers_generator.hpp>
#include <boost/beast/core/error.hpp>
#include <boost/beast/core/flat_buffer.hpp>
#include <boost/beast/http/basic_dynamic_body.hpp>
#include <boost/beast/http/chunk_encode.hpp>
#include <boost/beast/http/dynamic_body.hpp>
#include <boost/beast/http/empty_body.hpp>
#include <boost/beast/http/field.hpp>
#include <boost/beast/http/message_generator.hpp>
#include <boost/beast/http/serializer.hpp>
#include <boost/beast/http/status.hpp>
#include <boost/beast/http/string_body.hpp>
#include <boost/beast/http/write.hpp>
#include <boost/bind/bind.hpp>
#include <boost/program_options.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <chrono>
#include <exception>
#include <fstream>
#include <functional>
#include <iostream>
#include <optional>
#include <string>
#include <thread>
#include <vector>

#ifndef GIT_COMMIT_HASH
#define GIT_COMMIT_HASH "?"
#endif

void temp_worker_task(int worker_id) { std::cout << "Worker #" << worker_id << " started" << std::endl; }

void socket_timer_callback(const boost::system::error_code& ec,
                           std::map<std::string, boost::asio::ip::tcp::socket>* client_connections,
                           boost::asio::steady_timer* socket_check_timer) {
    if (!ec) {
        std::vector<std::string> clients_to_close;

        for (auto iterator = client_connections->begin(); iterator != client_connections->end(); iterator++) {
            // uuid = iterator -> first
            // socket_ = iterator -> second
            boost::system::error_code write_ec;

            // TCP doesn't have a method to detect if a client has closed a connection without writing to the socket if
            // the socket isn't watching for FIN So this is writing to the socket with a ping event to determine if the
            // client and server are still connected
            boost::asio::write(iterator->second, boost::asio::buffer((std::string) "event: ping" + "\n\n"), write_ec);

            if (!write_ec) {
                continue;
            }

            std::cout << "Socket to client " << iterator->first << " has been closed by the client: " << write_ec.what()
                      << "\n";
            iterator->second.close();
            clients_to_close.emplace_back(iterator->first);
        }

        std::for_each(clients_to_close.begin(), clients_to_close.end(),
                      [&client_connections](const std::string client_uuid) {
            std::cout << "Removing client connection for " << client_uuid << "\n";
            client_connections->erase(client_uuid);
        });
    } else {
        std::cout << "Socket check timer failed: " << ec.what() << std::endl;
    }

    socket_check_timer->expires_after(std::chrono::minutes(1));
    socket_check_timer->async_wait(
        boost::bind(socket_timer_callback, boost::asio::placeholders::error, client_connections, socket_check_timer));
}

void start_unix_socket_worker(std::map<std::string, boost::asio::ip::tcp::socket>& client_connections,
                              boost::asio::io_context& ioc) {
    std::cout << "Unix socket worker started" << std::endl;
    boost::asio::steady_timer socket_check_timer(ioc, std::chrono::minutes(1));
    socket_check_timer.async_wait(
        boost::bind(socket_timer_callback, boost::asio::placeholders::error, &client_connections, &socket_check_timer));
    ioc.run();
}

// Return a response for the given request.
template <class Body, class Allocator>
std::optional<boost::beast::http::message_generator> handle_request(
    boost::beast::http::request<Body, boost::beast::http::basic_fields<Allocator>>&& req,
    boost::asio::ip::tcp::socket& socket_) {
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
    std::map<std::string, boost::asio::ip::tcp::socket> client_connections;

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

    boost::asio::io_context ioc{1};
    boost::asio::ip::tcp::acceptor acceptor_{ioc, {boost::beast::net::ip::make_address("0.0.0.0"), 8081}};

    for (int i = 0; i < worker_count; i++) {
        worker_threads.emplace_back(temp_worker_task, i);
    }

    for (std::thread& thread : worker_threads) {
        thread.detach();
    }

    std::thread socket_worker_thread(start_unix_socket_worker, std::ref(client_connections), std::ref(ioc));
    socket_worker_thread.detach();

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

        // It appears that adding the \n\n to the end of the data string results in corrupted data
        // At least for Curl
        boost::asio::write(socket_, boost::asio::buffer((std::string) "data: ping" + "\n\n"), ec);
        if (ec) {
            std::cout << "Failed to write: " << ec.what() << std::endl;
            break;
        }

        std::string client_id = boost::uuids::to_string(boost::uuids::random_generator()());
        client_connections.emplace(client_id, std::move(socket_));

        boost::asio::write(client_connections.at(client_id), boost::asio::buffer((std::string) "data: pong" + "\n\n"),
                           ec);
    }

    return 0;
}
