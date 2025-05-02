cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(package REQUIRED CONFIG)

# Or, for projects that only export a .pc file:
# find_package(PkgConfig REQUIRED)
# pkg_check_modules(package REQUIRED IMPORTED_TARGET package)
# target_link_libraries(${PROJECT_NAME} PRIVATE PkgConfig::package)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE package::package)
