cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(fusepp REQUIRED CONFIG)

add_executable(${PROJECT_NAME} example.cpp)
target_link_libraries(${PROJECT_NAME} fusepp::fusepp)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
