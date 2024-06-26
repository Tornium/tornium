file(GLOB SOURCES *.cpp)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 20)
add_definitions(-DSOME_DEFINITION)

add_executable(scheduler ${SOURCES})
target_include_directories(scheduler PRIVATE ../include/)

# ---- Dependencies ----
include(../cmake/CPM.cmake)
CPMAddPackage(
	GITHUB_REPOSITORY jarro2783/cxxopts
	VERSION 3.0.0
	OPTIONS "CXXOPTS_BUILD_EXAMPLES NO" "CXXOPTS_BUILD_TESTS NO" "CXXOPTS_ENABLE_INSTALL YES"
)

find_package(Boost REQUIRED COMPONENTS url)
find_package(CURL REQUIRED)

if(CMAKE_BUILD_TYPE STREQUAL "Debug" OR CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo")
	CPMAddPackage(
		GITHUB_REPOSITORY libuv/libuv
		GIT_TAG v1.48.0
		OPTIONS "CXXOPTS_BUILD_EXAMPLES NO" "CXXOPTS_BUILD_TESTS NO" "CXXOPTS_ENABLE_INSTALL YES"
	)
elseif(CMAKE_BUILD_TYPE STREQUAL "Release")
	pkg_check_modules(scheduler libuv)
else()
	message(WARNING "Unknown build type: ${CMAKE_BUILD_TYPE}")
endif()

target_link_libraries(scheduler PRIVATE cxxopts uv curl ${Boost_LIBRARIES})

target_compile_options(scheduler PRIVATE -Wall -Wextra -Wshadow -Wconversion -Wsign-conversion -Wunused-parameter -Wno-long-long -pedantic)

# Get the current working branch
execute_process(
    COMMAND git rev-parse --abbrev-ref HEAD
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_BRANCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Get the latest commit hash
execute_process(
    COMMAND git describe --always --dirty
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    OUTPUT_VARIABLE GIT_COMMIT_HASH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
target_compile_definitions(scheduler PRIVATE "-DGIT_COMMIT_HASH=\"${GIT_COMMIT_HASH}\"")

set_target_properties(scheduler PROPERTIES
ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
