cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(rapids-cmake REQUIRED)
include(rapids-cpm)
rapids_cmake_write_version_file(version.txt)
