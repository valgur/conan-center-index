cmake_minimum_required(VERSION 3.15)
project(test_package C)

add_custom_command(OUTPUT test_package.c
    COMMAND re2c -W "${PROJECT_SOURCE_DIR}/syntax.re" -o test_package.c
)

add_executable(${PROJECT_NAME} test_package.c)
