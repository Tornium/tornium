#include "bucket.h"
#include "request.h"
#include "request_queue.h"
#include <algorithm>
#include <iostream>
#include <ostream>

std::map<uint32_t, scheduler::RequestBucket> request_buckets = {};

scheduler::RequestBucket::RequestBucket() : start_timestamp(std::time(0)) {}
scheduler::insertion_status scheduler::RequestBucket::try_emplace(scheduler::Request& request_) {
    const bool has_maxed_requests = bucket_requests.size() > REQUESTS_PER_BUCKET;

    if (request_.request_type == nice_type::user_request or request_.request_type == nice_type::high_priority_request) {
        if (has_maxed_requests) {
            // If the bucket is full and the request is to be immediately inserted,
            // The lowest niceness request will be popped and added to the request tree
            // while this request is executed immediately

            std::sort(bucket_requests.begin(), bucket_requests.end(),
                      [](const scheduler::Request first, const scheduler::Request second) {
                return first.nice < second.nice;
            });

            if (bucket_requests.back().request_type == nice_type::user_request) {
                // Don't need to check if vector is empty as it's already known that the size is `max_requests`
                scheduler::Request& popped_request = bucket_requests.back();
                bucket_requests.pop_back();
                scheduler::enqueue_request(popped_request);
            }
        }

        bucket_requests.push_back(request_);
        return insertion_status::immediate_insert;
    }

    return insertion_status::queued;
}

scheduler::RequestBucket scheduler::insert_request(scheduler::Request& request_) {
    request_buckets.try_emplace(request_.user_id, scheduler::RequestBucket());
    scheduler::RequestBucket bucket_ = request_buckets[request_.user_id];  // TODO: Use the iterator from try_emplace to get this

    switch(bucket_.try_emplace(request_)) {
        case scheduler::insertion_status::immediate_insert:
            std::cout << "HTTP request enqueued" << std::endl;
            // TODO: emplace request into active request queue
            break;
        case scheduler::insertion_status::queued:
            scheduler::enqueue_request(request_);
            break;
    }

    return bucket_;
}
