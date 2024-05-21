#include "message_queue.h"

#include <mutex>

void message_queue::queue::push(const message_queue::message& message_) {
    std::lock_guard<std::mutex> lock(mutex_);
    queued_messages.push(message_);
    cv_.notify_one();
}

message_queue::message message_queue::queue::pop() {
    std::unique_lock<std::mutex> lock(mutex_);

    while (queued_messages.empty()) {
        cv_.wait(lock);
    }

    message_queue::message message_ = queued_messages.front();
    queued_messages.pop();
    return message_;
}
