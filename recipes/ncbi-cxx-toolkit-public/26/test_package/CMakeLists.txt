cmake_minimum_required(VERSION 3.15)
project(PackageTest LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)

find_package(ncbi-cxx-toolkit-public REQUIRED CONFIG)

NCBI_begin_app(basic_sample)
  NCBI_sources(basic_sample)
  NCBI_uses_toolkit_libraries(xncbi)
NCBI_end_app()

add_executable(basic_sample2 basic_sample.cpp)
target_link_libraries(basic_sample2 PRIVATE ncbi-cxx-toolkit-public)

