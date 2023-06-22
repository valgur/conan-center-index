cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(di REQUIRED CONFIG)

add_executable(example example.cpp)
set_target_properties(example PROPERTIES CXX_STANDARD 14)
target_link_libraries(example di::di)
