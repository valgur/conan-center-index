cmake_minimum_required(VERSION 3.15)
project(test_package C)

find_package(X11 REQUIRED)

if(NOT _USING_CONAN_FindX11)
    message(FATAL_ERROR "Failed to load conan-findx11.cmake")
endif()

add_executable(${PROJECT_NAME}_cmake test_package.c)
target_link_libraries(${PROJECT_NAME}_cmake X11::X11)
