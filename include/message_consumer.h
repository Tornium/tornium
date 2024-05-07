#ifndef MESSAGE_CONSUMER_H
#define MESSAGE_CONSUMER_H

#include <pqxx/pqxx>

#include "message_queue.h"

namespace message_consumer {
void start_worker(message_queue::queue& queue);
}

#endif
