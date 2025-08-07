cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(CUDAToolkit REQUIRED)
find_package(cuda-cal REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE cuda-cal::cuda-cal CUDA::cuda_driver)
