cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C) # if the project is pure C
# project(test_package LANGUAGES CXX) # if the project uses C++

find_package(package REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE package::package)
