#ifndef CONFIG_H
#define CONFIG_H

#include <string>

namespace scheduler {
struct config {
    bool verbose = false;
    std::string socket_path = "/tmp/scheduler.sock";
};

/**
 * @brief Dump the configuration into stdout
 *
 * @param config_ Reference to the parsed configuration
 */
void dump_config(config& config_);
}
#endif
