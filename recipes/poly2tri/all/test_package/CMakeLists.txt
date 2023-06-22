cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(poly2tri REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE poly2tri::poly2tri)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
