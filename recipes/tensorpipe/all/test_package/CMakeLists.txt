cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Tensorpipe REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE tensorpipe)
if(TARGET tensorpipe_cuda)
    target_link_libraries(${PROJECT_NAME} PRIVATE tensorpipe_cuda)
    target_compile_definitions(${PROJECT_NAME} PRIVATE TP_WITH_CUDA)
endif()
