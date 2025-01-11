cmake_minimum_required(VERSION 3.15)
project(test_package C)

find_package(PkgConfig REQUIRED)
pkg_check_modules(nss REQUIRED IMPORTED_TARGET nss)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::nss)
