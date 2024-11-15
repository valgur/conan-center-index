cmake_minimum_required(VERSION 3.15.0)
project(test_package LANGUAGES CXX)

find_package(dsp-filters REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE dsp-filters::dsp-filters)
