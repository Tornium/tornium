#include "message_consumer.h"

#include <chrono>
#include <pqxx/pqxx>
#include <thread>

#include "message_queue.h"

#define MESSAGE_LIMIT 50

void message_consumer::start_worker(message_queue::queue& queue) {
    pqxx::connection connection_;

    for (;;) {
        pqxx::work transaction(connection_);
        int return_count = 0;

        for (auto [message_id, message_type_int, recipient, timestamp_str, event_str, data_string] :
             transaction.stream<std::string, int, std::optional<std::string>, std::string, std::optional<std::string>,
                                std::optional<std::string>>(
                 "DELETE FROM gatewaymessage USING (SELECT message_id, message_type, recipient, timestamp, event, data "
                 "FROM "
                 "gatewaymessage LIMIT " +
                 std::to_string(MESSAGE_LIMIT) +
                 " FOR UPDATE SKIP LOCKED) gm WHERE gm.message_id = gatewaymessage.message_id "
                 "RETURNING gatewaymessage.*")) {
            return_count++;

            if (!event_str.has_value() and !data_string.has_value()) {
                // No data to be trasnmitted in this message
                return;
            }

            std::tm timestamp_tm;
            strptime(timestamp_str.c_str(), "%Y-%m-%d %H:%M:%S", &timestamp_tm);
            time_t timestamp = mktime(&timestamp_tm);

            if (not recipient.has_value() and message_type_int != 3) {
                continue;
            }

            message_queue::message_type message_type_;
            switch (message_type_int) {
                case 0:
                    message_type_ = message_queue::message_type::direct;
                    break;
                case 1:
                    message_type_ = message_queue::message_type::user;
                    break;
                case 2:
                    // Not currently supported
                    return;

                    // message_type_ = message_queue::message_type::group;
                    // break;
                case 3:
                    message_type_ = message_queue::message_type::broadcast;
                    break;
            }

            const message_queue::message message_ = {
                message_id, message_type_, recipient, timestamp, event_str, data_string,
            };

            queue.push(message_);
        }

        transaction.commit();

        if (return_count < MESSAGE_LIMIT * 0.75) {
            // Sleep to prevent unnecessary system resource usage when no data is available
            std::this_thread::sleep_for(std::chrono::milliseconds(25));
        }
    }
}
