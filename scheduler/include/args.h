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

#ifndef ARGS_H
#define ARGS_H

#include "config.h"

namespace scheduler {

/**
 * @brief Parse the arguments passed into the CLI into the config struct
 *
 * @param argc Count of characters in arguments
 * @param argv Character array of arguments
 * @param config_ Reference to struct of globally shared configuration
 */
void parse_args(int argc, char* argv[], scheduler::config& config_);

}
#endif
