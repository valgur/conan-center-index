cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA)

find_package(cupqc REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE cuhash)
