cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Doxygen REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)

doxygen_add_docs(docs test_package.cpp ALL COMMENT "generate HTML")
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
