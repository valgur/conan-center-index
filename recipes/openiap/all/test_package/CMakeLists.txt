cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(openiap REQUIRED CONFIG)

add_executable(${PROJECT_NAME}_c test_package.c)
target_link_libraries(${PROJECT_NAME}_c PRIVATE openiap::openiap)
