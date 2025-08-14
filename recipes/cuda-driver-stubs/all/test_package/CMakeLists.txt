cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(CUDAToolkit REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} PRIVATE CUDA::cuda_driver)

# Check the FindCUDAToolkit.cmake wrapper output
foreach(pkg
        cudart cublas cudla cufile cufft curand cusolver cusparse cupti npp
        nvjpeg nvml-stubs nvptxcompiler nvrtc nvjitlink nvfatbin nvtx3 cuda-opencl culibos
        Thrust cub libcudacxx)
    if(${pkg}_COMPONENT_NAMES)
        string(REPLACE ";" " " libs "${${pkg}_COMPONENT_NAMES}")
    else()
        set(libs "${${pkg}_LIBRARIES}")
    endif()
    message(STATUS "${pkg} found: ${${pkg}_FOUND} | ${libs} | ${${pkg}_INCLUDE_DIRS}")
endforeach()

message(STATUS "CUDAToolkit_INCLUDE_DIRS: ${CUDAToolkit_INCLUDE_DIRS}")
message(STATUS "CUDAToolkit_LIBRARY_DIR: ${CUDAToolkit_LIBRARY_DIR}")

message(STATUS "CUDAToolkit_FOUND: ${CUDAToolkit_FOUND}")
message(STATUS "CUDAToolkit_VERSION: ${CUDAToolkit_VERSION}")
message(STATUS "CUDAToolkit_VERSION_MAJOR: ${CUDAToolkit_VERSION_MAJOR}")
message(STATUS "CUDAToolkit_VERSION_MINOR: ${CUDAToolkit_VERSION_MINOR}")
message(STATUS "CUDAToolkit_VERSION_PATCH: ${CUDAToolkit_VERSION_PATCH}")
message(STATUS "CUDAToolkit_BIN_DIR: ${CUDAToolkit_BIN_DIR}")
message(STATUS "CUDAToolkit_LIBRARY_ROOT: ${CUDAToolkit_LIBRARY_ROOT}")
message(STATUS "CUDAToolkit_TARGET_DIR: ${CUDAToolkit_TARGET_DIR}")
message(STATUS "CUDAToolkit_NVCC_EXECUTABLE: ${CUDAToolkit_NVCC_EXECUTABLE}")
