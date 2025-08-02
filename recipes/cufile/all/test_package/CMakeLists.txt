cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(cufile REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
if(TARGET CUDA::cufile_rdma)
    target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cufile_rdma)
else()
    target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cufile)
endif()
