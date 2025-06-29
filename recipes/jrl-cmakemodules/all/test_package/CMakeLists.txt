cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(jrl-cmakemodules REQUIRED)

include(stubs)
load_stubgen()

if(NOT EXISTS "${STUBGEN_MAIN_FILE}")
  message(FATAL_ERROR "${STUBGEN_MAIN_FILE} does not exist.")
else()
    message(STATUS "STUBGEN_MAIN_FILE ${STUBGEN_MAIN_FILE} exists.")
endif()
