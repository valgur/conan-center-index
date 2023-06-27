cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(baical-p7 REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE baical-p7::baical-p7)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
