cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(Thrust CONFIG REQUIRED)
thrust_create_target(Thrust::Cpp HOST CPP DEVICE CPP)
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} Thrust::Cpp)
