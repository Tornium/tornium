#ifndef BUCKET_H
#define BUCKET_H

#include "request.h"

#define REQUESTS_PER_BUCKET 6
#define BUCKET_INTERVAL 10

namespace scheduler {
enum class insertion_status { queued, immediate_insert };

class RequestBucket {
public:
	RequestBucket();
	insertion_status try_emplace(scheduler::Request& request_);

private:
	const std::time_t start_timestamp;
	std::vector<scheduler::Request> bucket_requests;
};

/**
 * @brief Insert request into a bucket and perform actions depending on priority
 *
 * @param request_ The request being made
 * @return Bucket the request is inserted into
 */
scheduler::RequestBucket insert_request(scheduler::Request &request_);
}

#endif
