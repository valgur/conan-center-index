cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(easyexif REQUIRED CONFIG)

add_executable(example example.cpp)
set_target_properties(example PROPERTIES CXX_STANDARD 11 CXX_STANDARD_REQUIRED ON)
target_link_libraries(example PRIVATE easyexif::easyexif)
