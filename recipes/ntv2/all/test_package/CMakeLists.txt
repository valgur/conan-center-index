cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(ntv2 CONFIG REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE ntv2::ntv2)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
