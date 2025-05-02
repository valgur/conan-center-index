cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(OpenXR REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
if (TARGET OpenXR::openxr_loader)
    target_link_libraries(${PROJECT_NAME} PRIVATE OpenXR::openxr_loader)
    target_compile_definitions(${PROJECT_NAME} PRIVATE HAVE_OPENXR_LOADER)
else()
    target_link_libraries(${PROJECT_NAME} PRIVATE OpenXR::headers)
endif()
