cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C CXX)

# FIXME: this is not the official way to find spirv-cross components
find_package(spirv-cross REQUIRED CONFIG)

if(TARGET spirv-cross-core)
    add_executable(${PROJECT_NAME}_cpp test_package.cpp)
    target_link_libraries(${PROJECT_NAME}_cpp PRIVATE spirv-cross-core)
endif()

if(TARGET spirv-cross-c)
    add_executable(${PROJECT_NAME}_c test_package.c)
    target_link_libraries(${PROJECT_NAME}_c PRIVATE spirv-cross-c)
endif()
