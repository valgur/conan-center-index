cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(rmlui REQUIRED CONFIG)

add_executable(example example.cpp)
target_link_libraries(example PRIVATE rmlui::rmlui)
set_property(TARGET example PROPERTY CXX_STANDARD 14)
