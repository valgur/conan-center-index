cmake_minimum_required(VERSION 3.15)
project(test_package CXX)
set(CMAKE_CXX_STANDARD 11)

find_package(libmemcached REQUIRED)

add_executable(${PROJECT_NAME} src/example.cpp)
#target_link_libraries(${PROJECT_NAME} PRIVATE libmemcached::libmemcached)
target_link_libraries(${PROJECT_NAME} libmemcached::libmemcached)
