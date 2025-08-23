cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA CXX)

find_package(cuco REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE cuco::cuco)
