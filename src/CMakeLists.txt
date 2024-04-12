file(GLOB SOURCES *.cpp)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_definitions(-DSOME_DEFINITION)

add_executable(dateway ${SOURCES})
target_include_directories(dateway PRIVATE ../include/)

find_package(Boost REQUIRED)
find_package(Boost REQUIRED COMPONENTS url)
find_package(Boost REQUIRED COMPONENTS program_options)
find_package(OpenSSL REQUIRED)
find_library(HIREDIS_LIB hiredis REQUIRED)
find_library(REDIS_PLUS_PLUS_LIB redis++ REQUIRED)

target_compile_options(dateway PRIVATE -Wall -Wextra -Wshadow -Wconversion -Wsign-conversion -Wunused-parameter -Wno-long-long -pedantic )
target_compile_features(dateway PRIVATE cxx_std_20)

include(FetchContent)
FetchContent_Declare(cpr GIT_REPOSITORY https://github.com/libcpr/cpr.git GIT_TAG 3b15fa82ea74739b574d705fea44959b58142eb8)
FetchContent_MakeAvailable(cpr)

FetchContent_Declare(json GIT_REPOSITORY https://github.com/nlohmann/json.git GIT_TAG 9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03)
FetchContent_MakeAvailable(json)

FetchContent_Declare(base64pp GIT_REPOSITORY https://github.com/matheusgomes28/base64pp.git GIT_TAG 432c94478fac1ab8b21beef9376b46bee20d8a5d)
FetchContent_MakeAvailable(base64pp)

target_link_libraries(dateway PRIVATE nlohmann_json::nlohmann_json cpr::cpr base64pp ${REDIS_PLUS_PLUS_LIB} ${HIREDIS_LIB} ${OPENSSL_LIBRARIES} ${Boost_LIBRARIES})

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
target_compile_definitions(dateway PRIVATE "-DGIT_COMMIT_HASH=\"${GIT_COMMIT_HASH}\"")


set_target_properties(dateway PROPERTIES
ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
