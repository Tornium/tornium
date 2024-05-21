#include "celery.h"

#include <base64pp/base64pp.h>
#include <sw/redis++/redis++.h>
#include <unistd.h>

#include <boost/asio/ip/host_name.hpp>
#include <boost/beast.hpp>
#include <boost/beast/core/detail/base64.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <iostream>
#include <nlohmann/json.hpp>

using namespace nlohmann;
using namespace sw::redis;

auto r = Redis("tcp://127.0.0.1:6379");
const std::string hostname = boost::asio::ip::host_name();

void send_task(std::string queue, std::string dumped_task, std::string task_id) { r.lpush(queue, dumped_task); }

void celery::send_guild_member_add(json& event) {
    std::cout << event << std::endl;

    const auto args_array = json::array({
        event["d"]["guild_id"],          // Server ID
        event["d"]["user"]["id"],        // User ID
        event["d"]["user"]["username"],  // User nickname - defaults to username when they first join a server
    });

    json body = json::array({args_array,      // args
                             json::object(),  // kwargs
                             {{"callbacks", nullptr}, {"errbacks", nullptr}, {"chain", nullptr}, {"chord", nullptr}}});

    std::string encoded_body = base64pp::encode_str(body.dump());
    const std::string task_uuid = boost::uuids::to_string(boost::uuids::random_generator()());

    json task_message;
    task_message["body"] = encoded_body;
    task_message["content-encoding"] = "utf-8";
    task_message["content-type"] = "application/json";
    task_message["headers"] = {
        {"lang", "cpp"},
        {"task", "tasks.gateway.on_member_join"},
        {"id", task_uuid},
        {"shadow", "null"},
        {"eta", nullptr},
        {"expires", nullptr},
        {"group", nullptr},
        {"group_index", nullptr},
        {"retries", 0},
        {"timelimit", json::array({15, nullptr})},
        {"root_id", task_uuid},
        {"parent_id", nullptr},
        {"argsrepr", "(" + (std::string)event["d"]["guild_id"] + ", " + (std::string)event["d"]["user"]["id"] +
                         ", \\'" + (std::string)event["d"]["user"]["username"] + "\\')"},
        {"kwargsrepr", "{}"},
        {"origin", "tornium-dateway@" + hostname},
        {"ignore_result", true},
        {"replaced_task_nesting", 0},
        {"stamped_headers", nullptr},
        {"stamps", json::object()},
    };
    task_message["properties"] = {{"correlation_id", task_uuid},
                                  {"delivery_mode", 2},
                                  {"delivery_info", {{"exchange", ""}, {"routing_key", "quick"}}},
                                  {"priority", 0},
                                  {"body_encoding", "base64"},
                                  {"delivery_tag", boost::uuids::to_string(boost::uuids::random_generator()())}};

    const std::string dumped_task = task_message.dump();
    send_task("quick", dumped_task, task_uuid);
}
