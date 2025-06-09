cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

find_package(fmi REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package_fmi${fmi_VERSION_MAJOR}.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE fmi::fmi)
