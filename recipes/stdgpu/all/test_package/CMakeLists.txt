cmake_minimum_required(VERSION 3.15)
project(test_package CXX)

find_package(stdgpu CONFIG REQUIRED)

# Skipping CUDA test as test_package can't conditionally add a tool_requires for nvcc
# if (STDGPU_BACKEND STREQUAL "cuda")
#     enable_language(CUDA)
#     add_executable(${PROJECT_NAME}_cuda test_package_cuda.cu)
#     target_link_libraries(${PROJECT_NAME}_cuda stdgpu::stdgpu)
# endif()
if (STDGPU_BACKEND STREQUAL "hip")
    enable_language(HIP)
    add_executable(${PROJECT_NAME}_hip test_package_hip.hip)
    target_link_libraries(${PROJECT_NAME}_hip stdgpu::stdgpu)
endif()
if (STDGPU_BACKEND STREQUAL "openmp")
    add_executable(${PROJECT_NAME}_openmp test_package_openmp.cpp)
    target_link_libraries(${PROJECT_NAME}_openmp stdgpu::stdgpu)
endif()

if (NOT stdgpu_VERSION_STRING STREQUAL "1.3.0")
    # v1.3.0 does not have stdgpu/device.h
    add_executable(${PROJECT_NAME}_basic test_package_basic.cpp)
    target_link_libraries(${PROJECT_NAME}_basic stdgpu::stdgpu)
endif()
