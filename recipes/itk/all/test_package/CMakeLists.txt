cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(ITK REQUIRED CONFIG)
find_package(HDF5 COMPONENTS CXX)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ITKCommon hdf5::hdf5_cpp)
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 11)
