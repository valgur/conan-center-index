cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(LLVM REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_14)

if(TARGET LLVMInterpreter)  # static libraries
    target_link_libraries(${PROJECT_NAME} PRIVATE
        LLVMInterpreter
        LLVMIRReader
        LLVMX86CodeGen
    )
else()  # shared library
    target_link_libraries(${PROJECT_NAME} LLVM)
endif()
