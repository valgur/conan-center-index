cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CUDA)

# if(NOT CMAKE_CUDA_ARCHITECTURES)
#   message(FATAL_ERROR "CMAKE_CUDA_ARCHITECTURES is not correctly defined")
# endif()

add_executable(${PROJECT_NAME} test_package.cu)
