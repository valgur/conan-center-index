cmake_minimum_required(VERSION 3.18)
project(test_package LANGUAGES CUDA CXX)

find_package(mathdx REQUIRED)

add_executable(${PROJECT_NAME} test_package.cu)
target_link_libraries(${PROJECT_NAME} PRIVATE mathdx::mathdx cufftdx::cufftdx_separate_twiddles_lut)
set_target_properties(${PROJECT_NAME} PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
