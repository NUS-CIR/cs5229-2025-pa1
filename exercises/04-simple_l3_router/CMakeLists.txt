cmake_minimum_required(VERSION 3.10)
project(simple_l3_router C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(DPDK REQUIRED libdpdk)

add_compile_options(-march=native)

include_directories(${DPDK_INCLUDE_DIRS})
link_directories(${DPDK_LIBRARY_DIRS})

add_executable(simple_l3_router simple_l3_router.c)
target_link_libraries(simple_l3_router ${DPDK_LIBRARIES})
