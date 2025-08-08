cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(cutensor REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cutensor)
if(TARGET CUDA::cutensorMg)
    target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cutensorMg)
endif()
