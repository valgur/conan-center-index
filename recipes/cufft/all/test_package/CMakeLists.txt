cmake_minimum_required(VERSION 3.18)
project(test_package LANGUAGES CUDA)

find_package(cufft REQUIRED)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cufftw)
set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
