cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(kainjow-mustache REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE kainjow-mustache::kainjow-mustache)
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 11)
