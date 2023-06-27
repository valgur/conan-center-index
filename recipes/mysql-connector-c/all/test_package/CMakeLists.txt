cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(mysql-connector-c REQUIRED CONFIG)
find_package(Threads)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} mysql-connector-c::mysql-connector-c ${CMAKE_DL_LIBS} ${CMAKE_THREAD_LIBS_INIT})
