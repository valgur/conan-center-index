cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(AdaptiveCpp REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
add_sycl_to_target(TARGET test_package SOURCES test_package.cpp)
# target_link_libraries(${PROJECT_NAME} PRIVATE AdaptiveCpp::acpp-rt)
