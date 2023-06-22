cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(box2d)

add_executable(test_package test_package.cpp)
target_link_libraries(test_package box2d::box2d)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
