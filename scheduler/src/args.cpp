#include <cxxopts.hpp>
#include "config.h"

#include "args.h"

void scheduler::parse_args(int argc, char* argv[], scheduler::config& config_) {
    cxxopts::Options options("scheduler", "A high performance Torn API call scheduler and proxy");

    options.add_options()
        // Options
        ("v,verbose", "verbose output", cxxopts::value<bool>()->default_value("false"))
        ("h,help", "print usage")
        ("dump", "dump config")
        // Positional arguments
        ("path", "path to the socket", cxxopts::value<std::string>()->default_value("/tmp/scheduler.sock"));
    options.parse_positional("path");
    auto result = options.parse(argc, argv);

    if (result.count("help")) {
        std::cout << options.help() << std::endl;
        exit(0);
    } else if (result.count("dump")) {
        scheduler::dump_config(config_);
    }

    config_.verbose = result["verbose"].as<bool>();
    config_.socket_path = result["path"].as<std::string>();
}
