#include <boost/asio/io_context.hpp>
#include <cxxopts.hpp>
#include <string>
#include <unistd.h>

#include "args.h"
#include "config.h"
#include "datagram_server.h"

int main(int argc, char* argv[]) {
    scheduler::config config_;
    scheduler::parse_args(argc, argv, config_);

    // TODO: Start API call processing thread

    ::unlink(config_.socket_path.c_str());
    boost::asio::io_context io_context_;
    scheduler::DatagramServer s_(io_context_, config_);
    s_.do_receive();

    io_context_.run();
}
