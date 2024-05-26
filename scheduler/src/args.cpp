// Copyright 2024 tiksan
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "args.h"

#include <cxxopts.hpp>
#include <fstream>

#include "config.h"

void scheduler::parse_args(int argc, char *argv[], scheduler::config &config_) {
    cxxopts::Options options("scheduler", "A high performance Torn API call scheduler and proxy");

    options.add_options()
        // Options
        ("v,verbose", "verbose output", cxxopts::value<bool>()->default_value("false"))("dump", "dump config")(
            "h,help", "print usage")("license", "print license")
        // Positional arguments
        ("path", "path to the socket", cxxopts::value<std::string>()->default_value("/tmp/scheduler.sock"));
    options.parse_positional("path");
    auto result = options.parse(argc, argv);

    if (result.count("help")) {
        std::cout << options.help() << std::endl;
        exit(0);
    } else if (result.count("license")) {
        std::ifstream f("../LICENSE-short");
        std::cout << f.rdbuf() << std::endl;
        exit(0);
    } else if (result.count("dump")) {
        scheduler::dump_config(config_);
    }

    config_.verbose = result["verbose"].as<bool>();
    config_.socket_path = result["path"].as<std::string>();
}
