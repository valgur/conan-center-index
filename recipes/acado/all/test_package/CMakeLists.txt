cmake_minimum_required(VERSION 3.15)
project(test_package CXX C)

set(CMAKE_CXX_STANDARD 11)

find_package(ACADO REQUIRED CONFIG)

add_executable(codegen codegen.cpp)
target_link_libraries(codegen PRIVATE ACADO::ACADO)

set(CODEGEN_DIR ${CMAKE_CURRENT_BINARY_DIR}/generated_code)

set(codegen_GENERATED_FILES
    ${CODEGEN_DIR}/acado_common.h
    ${CODEGEN_DIR}/acado_solver.c
    ${CODEGEN_DIR}/acado_integrator.c
    ${CODEGEN_DIR}/acado_qpoases_interface.hpp
    ${CODEGEN_DIR}/acado_qpoases_interface.cpp
    ${CODEGEN_DIR}/acado_auxiliary_functions.h
    ${CODEGEN_DIR}/acado_auxiliary_functions.c
)

set(ACADO_TEMPLATE_PATHS ${acado_PACKAGE_FOLDER_RELEASE}/include/acado/code_generation/templates)
#message(FATAL_ERROR ${ACADO_TEMPLATE_PATHS})
add_custom_command(
  OUTPUT ${codegen_GENERATED_FILES}
  COMMAND ACADO_TEMPLATE_PATHS=${ACADO_TEMPLATE_PATHS} codegen ${CODEGEN_DIR}
  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
  DEPENDS codegen)

add_library(mpc_codegen STATIC ${codegen_GENERATED_FILES})
target_include_directories(mpc_codegen SYSTEM PUBLIC ${CODEGEN_DIR})

add_executable(test_package test_package.cpp)
target_link_libraries(test_package PRIVATE mpc_codegen)
