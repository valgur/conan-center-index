cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(atk REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE atk::atk)

if (CMAKE_SYSTEM_NAME STREQUAL "Windows")
    find_package(glib CONFIG REQUIRED)
    target_link_libraries(${PROJECT_NAME} PRIVATE glib::glib-2.0)
else()
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(glib-2.0 REQUIRED IMPORTED_TARGET glib-2.0)
    target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::glib-2.0)
endif()
