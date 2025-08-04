cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(cuDNN REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE cuDNN::cudnn_graph)

if(TARGET cuDNN::cudnn_ops)
    add_executable(${PROJECT_NAME}_legacy test_package_legacy.c)
    target_link_libraries(${PROJECT_NAME}_legacy PRIVATE cuDNN::cudnn_ops)
endif()
