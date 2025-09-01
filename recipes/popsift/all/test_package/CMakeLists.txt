cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX CUDA)

find_package(PopSift REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE PopSift::popsift)
set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_RESOLVE_DEVICE_SYMBOLS ON)
