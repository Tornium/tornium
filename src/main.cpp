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
#include <exception>
#include <fstream>
#include <iostream>
#include <optional>
#include <pqxx/pqxx>
#include <string>
#include <thread>
#include <vector>

#include "http.cpp"
#include "message_consumer.h"
#include "message_queue.h"
#include "socket_watcher.h"

#ifndef GIT_COMMIT_HASH
#define GIT_COMMIT_HASH "?"
#endif

void temp_worker_task(int worker_id, message_queue::queue& queue_,
                      std::map<std::string, boost::asio::ip::tcp::socket>& client_connections) {
    std::cout << "Worker #" << worker_id << " started" << std::endl;

    for (;;) {
        const message_queue::message message_ = queue_.pop();
        std::cout << "Processing message " << message_.message_id << " for " << message_.message_id << std::endl;

        boost::beast::error_code ec;
        std::string message_string;

        if (message_.event.has_value() and message_.data.has_value()) {
            message_string = "event: " + message_.event.value() + "\ndata: " + message_.data.value() + "\n\n";
        } else if (message_.event.has_value() and not message_.data.has_value()) {
        } else if (not message_.event.has_value() and message_.data.has_value()) {
        } else {
            std::cout << "Message ID " << message_.message_id << " has an invalid message body\n";
            continue;
        }

        boost::asio::write(client_connections.at("05f867766ea446c0affe0af54713bcd7"),
                           boost::asio::buffer(message_string), ec);

        if (ec) {
            std::cout << "Failed to write: " << ec.what() << std::endl;
            continue;
        }
    }
}

int main(int argc, char* argv[]) {
    int worker_count = 1;
    int max_workers = 1;
    std::vector<std::thread> worker_threads;
    std::map<std::string, boost::asio::ip::tcp::socket> client_connections;
    std::map<int, std::vector<std::string>> user_client_map;

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
    pqxx::connection postgres_connection;
    message_queue::queue queue_;

    for (int i = 0; i < worker_count; i++) {
        worker_threads.emplace_back(temp_worker_task, i, std::ref(queue_), std::ref(client_connections));
    }

    for (std::thread& thread : worker_threads) {
        thread.detach();
    }

    std::thread socket_worker_thread(socket_watcher::start_unix_socket_worker, std::ref(client_connections),
                                     std::ref(ioc));
    socket_worker_thread.detach();

    std::thread message_consumer_thread(message_consumer::start_worker, std::ref(queue_));
    message_consumer_thread.detach();

    for (;;) {
        boost::asio::ip::tcp::socket socket_{ioc};
        acceptor_.accept(socket_);

        boost::beast::error_code ec;
        boost::beast::flat_buffer buffer;

        boost::beast::http::request<boost::beast::http::string_body> request_;
        boost::beast::http::read(socket_, buffer, request_, ec);

        if (ec == boost::beast::http::error::end_of_stream) {
            continue;
        } else if (ec) {
            std::cerr << "HTTP read failed: " << ec.what() << std::endl;
            continue;
        }

        // Handle request
        auto [msg, client_id] = http::handle_request(std::move(request_), socket_, postgres_connection);

        // Send the response
        if (msg.has_value()) {
            boost::beast::write(socket_, msg.value(), ec);
            continue;
        }

        if (ec) {
            std::cout << "Failed to write: " << ec.what() << std::endl;
            continue;
        }

        // It appears that adding the \n\n to the end of the data string results in corrupted data
        // At least for Curl
        boost::asio::write(socket_, boost::asio::buffer((std::string) "data: ping" + "\n\n"), ec);
        if (ec) {
            std::cout << "Failed to write: " << ec.what() << std::endl;
            continue;
        }

        if (client_connections.contains(client_id.value())) {
            // Close the pre-existing connection if one for the client already exists
            boost::asio::write(
                client_connections.at(client_id.value()),
                boost::asio::buffer((std::string) "event: close\ndata: new socket for same client" + "\n\n"), ec);
            std::cout << "Closing pre-existing client socket for client " << client_id.value() << std::endl;

            if (ec) {
                std::cout << "Failed to write (continue): " << ec.what() << std::endl;
            }

            client_connections.at(client_id.value()).close();
            client_connections.erase(client_id.value());
        }

        client_connections.emplace(client_id.value(), std::move(socket_));
        boost::asio::write(client_connections.at(client_id.value()),
                           boost::asio::buffer((std::string) "data: pong" + "\n\n"), ec);
    }

    return 0;
}
