# Tornium Scheduler
Tornium Scheduler is a high-performance Torn API call scheduler. The goals of this project are:
- Handle thousands (if not tens of thousands) of API calls per minute
- Handle these API calls in a performant manner without many threads
- Prioritize API calls given a provided API call priority

## Requirements
Tornium Scheduler requires the following to build the software:
- A C++20 compatible compiler such as GCC and Clang
- CMake
- Boost 1.81.0 or greater
- libcurl
- libuv

Additionally, Tornium Scheduler is only set up for a Linux/Unix or MacOS file system at this time.

## Installation
- Clone the monorepo: `git clone https://github.com/Tornium/tornium.git`
- Navigate to the scheduler directory: `cd scheduler/`
- Create the build directory: `mkdir build && cd build`
- Run CMake: `cmake --DCMAKE_BUILD_TYPE=Release ..`
- Run Make: `make`

## Usage
You can start the application with `./bin/scheduler` while within the build directory. See `./bin/scheduler --help` for more information.

Requests can be sent to the datagram socket under `/tmp/scheduler.sock`. An example of the format can be found below using netcat.

```
echo "PRIORITY\nhttps://api.torn.com/API_CALL\nREQUESTING_USER\nMAX_RETRIES\n\n" | nc -uU /tmp/scheduler.sock -N -w 1
echo "10\nhttps://api.torn.com/user/1?selections=&key=\n238226\n1\n\n" | nc -uU /tmp/scheduler.sock -N -w 1
```

Responses to the API calls will be sent to [NYI].

## License
Tornium Scheduler is licensed under Apache 2.0.

```
Copyright 2024 tiksan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
