cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(OpenMP CONFIG REQUIRED)

add_executable(test_package test_package.cpp)
target_link_libraries(test_package OpenMP::OpenMP_CXX)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
