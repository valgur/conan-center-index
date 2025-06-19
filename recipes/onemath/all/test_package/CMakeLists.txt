cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(oneMath REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE onemath::onemath)
#if(TARGET ONEMATH::onemath)
#    target_link_libraries(${PROJECT_NAME} PRIVATE ONEMATH::onemath)
#elseif(TARGET ONEMATH::onemath_blas_mklcpu)
#    target_link_libraries(${PROJECT_NAME} PRIVATE ONEMATH::onemath_blas_mklcpu)
#elseif(TARGET ONEMATH::onemath_blas_netlib)
#    target_link_libraries(${PROJECT_NAME} PRIVATE ONEMATH::onemath_blas_netlib)
#elseif(TARGET ONEMATH::onemath_blas_cublas)
#    target_link_libraries(${PROJECT_NAME} PRIVATE ONEMATH::onemath_blas_cublas)
#else()
#    message(FATAL_ERROR "No valid oneMath BLAS target found")
#endif()
#
