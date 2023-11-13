cmake_minimum_required(VERSION 3.15)
project(test_package C)

find_package(Python REQUIRED COMPONENTS Interpreter Development)

add_executable(${PROJECT_NAME} py3/test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE Python::Python)

if(BUILD_MODULE)
    add_library(spam MODULE py3/test_module.c)
    target_link_libraries(spam PRIVATE Python::Python)

    set_property(TARGET spam PROPERTY PREFIX "")
    if(MSVC)
        set_property(TARGET spam PROPERTY SUFFIX "$<$<CONFIG:DEBUG>:_d>.pyd")
    endif()
    python3_add_library(spam2 py3/test_module.c)
endif()
