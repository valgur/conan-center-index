cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(PkgConfig REQUIRED)
pkg_check_modules(coinmumps REQUIRED IMPORTED_TARGET coinmumps)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::coinmumps)
