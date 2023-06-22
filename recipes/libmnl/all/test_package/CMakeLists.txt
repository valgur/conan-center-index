cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(libmnl REQUIRED CONFIG)

add_executable(example example.cpp)
target_link_libraries(example PRIVATE libmnl::libmnl)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
