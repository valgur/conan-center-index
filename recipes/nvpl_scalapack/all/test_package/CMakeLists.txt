cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(nvpl_scalapack REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE
    nvpl::scalapack_lp64
    nvpl::blacs_lp64_openmpi
    nvpl::lapack_lp64_seq
)
