cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(tclap REQUIRED CONFIG)

add_executable(test_package test.cpp)
target_link_libraries(test_package tclap::tclap)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
