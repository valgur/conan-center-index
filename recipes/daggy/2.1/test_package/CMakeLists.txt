cmake_minimum_required(VERSION 3.15)
project(DaggyPackageTest LANGUAGES CXX)

find_package(DaggyCore REQUIRED CONFIG)

add_executable(test_package test.cpp)
target_link_libraries(test_package daggy::DaggyCore)
