cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(Qt${QT_MAJOR}Keychain CONFIG REQUIRED)

add_executable(test_package test_package.cpp)
target_link_libraries(test_package Qt${QT_MAJOR}Keychain::Qt${QT_MAJOR}Keychain)
