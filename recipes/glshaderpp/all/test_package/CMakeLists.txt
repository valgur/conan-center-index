cmake_minimum_required(VERSION 3.15)
project(PackageTest CXX)

find_package(glew CONFIG REQUIRED)
find_package(glshaderpp CONFIG REQUIRED)

add_executable(${PROJECT_NAME} example.cpp)
target_link_libraries(${PROJECT_NAME} glshaderpp::glshaderpp GLEW::GLEW)
set_target_properties(${PROJECT_NAME} PROPERTIES CXX_STANDARD 17 CXX_STANDARD_REQUIRED ON)
