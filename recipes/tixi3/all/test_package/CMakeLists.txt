cmake_minimum_required(VERSION 3.15)
project(Tixi-Conan-TestPackage CXX)

find_package(tixi3 REQUIRED)

add_executable(tixi3_conan_test main.cpp)
target_link_libraries(tixi3_conan_test PRIVATE tixi3)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
