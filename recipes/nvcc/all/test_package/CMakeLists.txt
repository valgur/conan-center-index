cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA)

add_executable(${PROJECT_NAME} test_package.cu)
