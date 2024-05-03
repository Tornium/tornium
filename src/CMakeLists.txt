file(GLOB SOURCES *.cpp)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 20)
add_definitions(-DSOME_DEFINITION)

add_executable(sse-proxy ${SOURCES})
target_include_directories(sse-proxy PRIVATE ../include/)

find_package(Boost REQUIRED)
find_package(Boost REQUIRED COMPONENTS program_options)

target_compile_options(sse-proxy PRIVATE -Wall -Wextra -Wshadow -Wconversion -Wsign-conversion -Wunused-parameter -Wno-long-long -pedantic )
target_compile_features(sse-proxy PRIVATE cxx_std_20)

include(FetchContent)

FetchContent_Declare(libpqxx GIT_REPOSITORY https://github.com/jtv/libpqxx.git GIT_TAG 2ffb711bc4e9b086bf0c549a9c22b19f61ab5476)
FetchContent_MakeAvailable(libpqxx)

target_link_libraries(sse-proxy PRIVATE pqxx ${Boost_LIBRARIES})

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
