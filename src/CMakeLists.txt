file(GLOB SOURCES *.cpp)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_definitions(-DSOME_DEFINITION)

add_executable(sse-proxy ${SOURCES})
target_include_directories(sse-proxy PRIVATE ../include/)

find_package(Boost REQUIRED)
find_package(Boost REQUIRED COMPONENTS program_options)
find_package(OpenSSL REQUIRED)

target_compile_options(sse-proxy PRIVATE -Wall -Wextra -Wshadow -Wconversion -Wsign-conversion -Wunused-parameter -Wno-long-long -pedantic )
target_compile_features(sse-proxy PRIVATE cxx_std_20)

include(FetchContent)

FetchContent_Declare(base64pp GIT_REPOSITORY https://github.com/matheusgomes28/base64pp.git GIT_TAG 432c94478fac1ab8b21beef9376b46bee20d8a5d)
FetchContent_MakeAvailable(base64pp)

include_directories(${OPENSSL_INCLUDE_DIR})

target_link_libraries(sse-proxy PRIVATE base64pp ${Boost_LIBRARIES} ${OPENSSL_LIBRARIES})

#Get the current working branch
execute_process(
    COMMAND git rev-parse --abbrev-ref HEAD
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_BRANCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
#Get the latest commit hash
execute_process(
    COMMAND git describe --always --dirty
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_COMMIT_HASH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
target_compile_definitions(sse-proxy PRIVATE "-DGIT_COMMIT_HASH=\"${GIT_COMMIT_HASH}\"")


set_target_properties(sse-proxy PROPERTIES
ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
