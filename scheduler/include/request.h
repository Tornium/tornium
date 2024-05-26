#ifndef REQUEST_H
#define REQUEST_H

#include <cstdint>
#include <ctime>
#include <map>
#include <optional>
#include <string>
#include <vector>

namespace scheduler {
enum class nice_type { user_request, high_priority_request, generic_request };

struct Request {
    int8_t nice;
    std::string endpoint;
    std::string endpoint_id;
    uint32_t user_id;
    uint8_t remaining_retries;

    std::vector<Request> linked_requests;
    
    std::time_t time_received;
    std::optional<std::time_t> time_scheduled;
    nice_type request_type;
};

std::optional<Request> parse_request(char* data_, const size_t& bytes_received, const size_t& buffer_max_length);
std::optional<Request> request_by_path(std::multimap<std::string, Request&>& requests_map, std::string path);

/**
 * @brief Try to insert the request into the list of all received requests that haven't been completed
 *
 * @param requests_map Reference to the multimap of request
 * @param request_ Reference to the request received
 * @return True if the request has been added to the multimap, False if the request wasn't able to be added and needs to be linked to an existing request
 */
bool enqueue_request(std::multimap<std::string, Request&>& requests_map, Request& request_);
bool retry_request(Request& request_);

size_t requests_count(std::multimap<std::string, Request&>& requests_map);
void remove_request(std::multimap<std::string, Request&>& requests_map, std::string request_key);
void decrement_niceness(std::multimap<std::string, Request&>& requests_map);
}

#endif
