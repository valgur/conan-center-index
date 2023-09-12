<<<<<<<< HEAD:recipes/cassandra-cpp-driver/all/test_v1_package/CMakeLists.txt
cmake_minimum_required(VERSION 3.1)
========
cmake_minimum_required(VERSION 3.15)
>>>>>>>> upstream/master:recipes/soplex/all/test_v1_package/CMakeLists.txt
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(TARGETS)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../test_package/
                 ${CMAKE_CURRENT_BINARY_DIR}/test_package/)
