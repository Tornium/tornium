#ifndef MESSAGE_QUEUE_H
#define MESSAGE_QUEUE_H

#include <condition_variable>
#include <ctime>
#include <optional>
#include <queue>
#include <string>

namespace message_queue {
enum class message_type {
    direct = 0,
    user = 1,
    group = 2,
    broadcast = 3,
};

struct message {
    std::string message_id;
    message_type message_type_;
    std::optional<std::string> recipient;
    std::time_t timestamp;
    std::optional<std::string> event;
    std::optional<std::string> data;
};

class queue {
   public:
    void push(const message& message_);
    message pop();

   private:
    std::queue<message> queued_messages;
    mutable std::mutex mutex_;
    std::condition_variable cv_;
};
}  // namespace message_queue

#endif
