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
