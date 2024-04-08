#include <cpr/cpr.h>

#include <boost/asio.hpp>
#include <boost/asio/io_service.hpp>
#include <boost/asio/ssl.hpp>
#include <boost/asio/strand.hpp>
#include <boost/program_options.hpp>
#include <boost/smart_ptr/make_shared_array.hpp>
#include <exception>
#include <fstream>
#include <iostream>
#include <memory>
#include <nlohmann/json.hpp>

#include "shard.h"

#ifndef GIT_COMMIT_HASH
#define GIT_COMMIT_HASH "?"
#endif

using namespace ws_shard;

int main(int argc, char *argv[]) {
    std::string discord_token;
    size_t shard_count = 0;
    std::string gateway_url;

    try {
        std::string config_file;

        boost::program_options::options_description generic("Generic options");
        generic.add_options()("version,v", "Return version string")("help,h", "Return help message")(
            "config,c", boost::program_options::value<std::string>(&config_file)->default_value("dateway.cfg"),
            "Path to configuration file")("print-config", "Print the configuration");

        boost::program_options::options_description config("Configuration");
        config.add_options()("discord_token", boost::program_options::value<std::string>(&discord_token),
                             "Discord bot token")("shard_count", boost::program_options::value<size_t>(&shard_count),
                                                  "Number of shards for the bot");

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
            return 0;
        } else {
            store(boost::program_options::parse_config_file(ifs, config_file_options), vm);
            notify(vm);
        }

        if (vm.count("help")) {
            std::cout << "Usage\n\tdateway [options]\n" << cmdline_options << std::endl;
            return 0;
        } else if (vm.count("version")) {
            std::cout << "Tornium Dateway version 0.1.0-" << GIT_COMMIT_HASH << std::endl;
            return 0;
        } else if (vm.count("print-config")) {
            std::cout << "Discord token: " << discord_token << std::endl;
            std::cout << "Shard count: " << shard_count << std::endl;
            return 0;
        }
    } catch (std::exception e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }

    boost::asio::io_context io_context;
    boost::asio::ssl::context ctx{boost::asio::ssl::context::tlsv12_client};
    ctx.set_default_verify_paths();

    cpr::Response gateway_response =
        cpr::Get(cpr::Url{"https://discord.com/api/v10/gateway/bot"},
                 cpr::Header{{"Content-Type", "application/json"}, {"Authorization", "Bot " + discord_token}});
    const nlohmann::json gateway_response_object = nlohmann::json::parse(gateway_response.text);

    if (gateway_response_object.contains("code")) {
        std::cerr << "Failed to retrieve gateway details" << std::endl;
        std::cout << gateway_response_object << std::endl;
        return 1;
    }

    if (shard_count == 0) {
        shard_count = gateway_response_object["shards"];
        std::cout << "Setting shard count to " << shard_count << std::endl;
    }

    gateway_url = gateway_response_object["url"];
    std::cout << "Setting gateway URL to " << gateway_url << std::endl;

    boost::asio::ip::tcp::resolver::results_type resolved_gateway;

    try {
        boost::asio::ip::tcp::resolver resolver_ = boost::asio::ip::tcp::resolver(boost::asio::make_strand(io_context));
        resolved_gateway = resolver_.resolve(gateway_url.substr(6), "443");
    } catch (std::exception e) {
        std::cerr << "Failed to resolve " << gateway_url << std::endl;
        std::cerr << e.what() << std::endl;
        return 1;
    }

    for (size_t shard_id = 0; shard_id < shard_count; shard_id++) {
        std::cout << "Creating shard ID " << shard_id << std::endl;
        const auto s = std::make_shared<shard>(io_context, ctx, shard_id, gateway_url);
        s->run(resolved_gateway);
    }

    auto keep_alive_work = std::make_shared<boost::asio::io_service::work>(io_context);
    io_context.run();

    return 0;
}
