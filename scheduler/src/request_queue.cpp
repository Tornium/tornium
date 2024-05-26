#include "request_queue.h"
#include "request.h"
#include <algorithm>

// The vector of requests is required to be sorted by niceness and then time added
static std::map<uint32_t, std::vector<scheduler::Request*>> request_queue = {};

bool compare_request_priority(const scheduler::Request* r1, const scheduler::Request* r2) {
    // TODO: Add secondary sort for time added if niceness are equal
    //
    // Lower priority number is higher priority
    return r1 -> nice < r2 -> nice;
}

void scheduler::enqueue_request(scheduler::Request &request_) {
    std::vector<scheduler::Request*>& user_request_queue = request_queue.try_emplace(request_.user_id, std::vector<Request*> {}).first -> second;

    auto sorting_iterator = std::lower_bound(user_request_queue.begin(), user_request_queue.end(), &request_, compare_request_priority);
    user_request_queue.insert(sorting_iterator, &request_);
}
