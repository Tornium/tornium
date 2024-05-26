#include "config.h"
#include <iostream>

void scheduler::dump_config(scheduler::config& config_) {
    std::cout << "====== Config Dump =====\n";
    std::cout << "Verbose: " << config_.verbose << "\n";
    std::cout << "Socket Path: " << config_.socket_path << "\n";
    std::cout << "========================\n\n";
}
