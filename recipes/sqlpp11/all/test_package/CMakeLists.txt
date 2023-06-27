cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(Sqlpp11 REQUIRED CONFIG)

add_executable(example example.cpp)
set_property(TARGET example PROPERTY CXX_STANDARD 14)
target_link_libraries(example sqlpp11::sqlpp11)
