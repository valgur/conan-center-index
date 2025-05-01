cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(PkgConfig REQUIRED)
pkg_check_modules(lttng-ust-tracepoint REQUIRED IMPORTED_TARGET lttng-ust-tracepoint)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::lttng-ust-tracepoint)
