cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(flatc REQUIRED CONFIG)

build_flatbuffers("test_package.fbs" "" flatbuffers "" "${CMAKE_CURRENT_BINARY_DIR}" "" "")

add_executable(${PROJECT_NAME} ${CMAKE_CURRENT_BINARY_DIR}/test_package_generated.h test_package.cpp)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
