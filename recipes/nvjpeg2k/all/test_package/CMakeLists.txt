cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(nvjpeg2k REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::nvjpeg2k)
