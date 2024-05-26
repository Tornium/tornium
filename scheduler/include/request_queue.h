#ifndef REQUEST_QUEUE_H
#define REQUEST_QUEUE_H

#include "request.h"

namespace scheduler {
/**
 * @brief Insert a request into the user's sorted vector of enqueued requests
 *
 * @param request_ Reference to the request
 */
void enqueue_request(scheduler::Request& request_);
}

#endif
