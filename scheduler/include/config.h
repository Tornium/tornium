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
void dump_config(config &config_);
}  // namespace scheduler
#endif
