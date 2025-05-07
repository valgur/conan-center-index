cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

find_package(laszip REQUIRED CONFIG)

if(laszip_VERSION GREATER_EQUAL "3.0.0")
    add_executable(${PROJECT_NAME} test_package.c)
else()
    add_executable(${PROJECT_NAME} test_package_old.cpp)
endif()
target_link_libraries(${PROJECT_NAME} PRIVATE laszip::laszip)
