if(CMAKE_FIND_PACKAGE_NAME STREQUAL "CUDAToolkit" AND TARGET CUDA::toolkit)
    return()
elseif(CMAKE_FIND_PACKAGE_NAME STREQUAL "CUDA" AND DEFINED CUDA_SDK_ROOT_DIR)
    return()
else()
    include_guard()
endif()

# Find all packagages supported by FindCUDAToolkit.cmake as of CMake v4.0.3
foreach(pkg
        cudart cublas cudla cufile cufft curand cusolver cusparse cupti npp
        nvjpeg nvml-stubs nvptxcompiler nvrtc nvjitlink nvfatbin nvtx3 cuda-opencl
        culibos cuda-crt CCCL libcudacxx Thrust cub)
    find_package(${pkg} QUIET)
    if(NOT ${pkg}_FOUND)
        continue()
    endif()
    list(APPEND CUDAToolkit_INCLUDE_DIRS ${${pkg}_INCLUDE_DIRS})
    list(APPEND CUDAToolkit_LIBRARIES ${${pkg}_LIBARIES})  # Not an official variable
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib" ABSOLUTE)
        list(APPEND CUDAToolkit_LIBRARY_DIR "${_lib_dir}")
    endif()
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib/stubs")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib/stubs" ABSOLUTE)
        list(APPEND CUDAToolkit_LIBRARY_DIR "${_lib_dir}")
    endif()
endforeach()

if(NOT TARGET CUDA::toolkit)
    add_library(CUDA::toolkit IMPORTED INTERFACE)
    target_include_directories(CUDA::toolkit SYSTEM INTERFACE "${CUDAToolkit_INCLUDE_DIRS}")
    target_link_directories(CUDA::toolkit INTERFACE "${CUDAToolkit_LIBRARY_DIR}")
endif()


# Find NVCC and set some expected paths based on it
set(CUDAToolkit_BIN_DIR)
set(CUDAToolkit_TARGET_DIR)
set(CUDAToolkit_LIBRARY_ROOT)
if(FALSE AND DEFINED ENV{CUDACXX})
    set(CUDAToolkit_NVCC_EXECUTABLE "$ENV{CUDACXX}")
else()
    find_program(CUDAToolkit_NVCC_EXECUTABLE nvcc QUIET)
endif()
if(CUDAToolkit_NVCC_EXECUTABLE)
    # Parse nvcc version from nvcc --version output:
    #   nvcc: NVIDIA (R) Cuda compiler driver
    #   Copyright (c) 2005-2025 NVIDIA Corporation
    #   Built on Tue_May_27_02:21:03_PDT_2025
    #   Cuda compilation tools, release 12.9, V12.9.86
    #   Build cuda_12.9.r12.9/compiler.36037853_0
    execute_process(COMMAND ${CUDAToolkit_NVCC_EXECUTABLE} --version OUTPUT_VARIABLE _nvcc_version_output)
    if("${_nvcc_version_output}" MATCHES "release ([0-9]+\\.[0-9]+)," AND
       CMAKE_MATCH_1 STREQUAL "${CUDAToolkit_VERSION_MAJOR}.${CUDAToolkit_VERSION_MINOR}")
        get_filename_component(CUDAToolkit_BIN_DIR "${CUDAToolkit_NVCC_EXECUTABLE}" DIRECTORY)
        get_filename_component(CUDAToolkit_ROOT "${CUDAToolkit_BIN_DIR}" DIRECTORY)
        set(CUDAToolkit_TARGET_DIR "${CUDAToolkit_ROOT}")
        set(CUDAToolkit_LIBRARY_ROOT "${CUDAToolkit_ROOT}/lib")
    else()
        if(NOT CUDAToolkit_FIND_QUIETLY)
            message(WARNING "Found NVCC at ${CUDAToolkit_NVCC_EXECUTABLE},"
                            " but its version '${CMAKE_MATCH_1}' did not match cuda-driver-stubs version of '${CUDAToolkit_VERSION}'.")
        endif()
        set(CUDAToolkit_NVCC_EXECUTABLE "")
    endif()
endif()

# Set variables for compatibility with the legacy FindCUDA.cmake module
if(CMAKE_FIND_PACKAGE_NAME STREQUAL "CUDA")
    # major and minor are set by CMakeDeps
    # set(CUDA_VERSION_MAJOR "${CUDAToolkit_VERSION_MAJOR}")
    # set(CUDA_VERSION_MINOR "${CUDAToolkit_VERSION_MINOR}")
    set(CUDA_VERSION_STRING "${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}")
    set(CUDA_VERSION "${CUDA_VERSION_MAJOR}.${CUDA_VERSION_MINOR}")
    set(CUDA_TOOLKIT_ROOT_DIR "${CUDAToolkit_ROOT}")
    set(CUDA_SDK_ROOT_DIR "${CUDAToolkit_ROOT}")
    set(CUDA_INCLUDE_DIRS "${CUDAToolkit_INCLUDE_DIRS}")
    set(CUDA_LIBRARIES "${CUDAToolkit_LIBRARIES}")

    if(TARGET CUDA::cufft)
        set(CUDA_CUFFT_LIBRARIES CUDA::cufft)
    endif()
    if(TARGET CUDA::cublas)
        set(CUDA_CUBLAS_LIBRARIES CUDA::cublas)
    endif()
    if(TARGET CUDA::cupti)
        set(CUDA_cupti_LIBRARY CUDA::cupti)
    endif()
    if(TARGET CUDA::curand)
        set(CUDA_curand_LIBRARY CUDA::curand)
    endif()
    if(TARGET CUDA::cusparse)
        set(CUDA_cusparse_LIBRARY CUDA::cusparse)
    endif()
    if(TARGET npp::npp)
        set(CUDA_npp_LIBRARY npp::npp)
    endif()
    if(TARGET CUDA::nppc)
        set(CUDA_nppc_LIBRARY CUDA::nppc)
    endif()
    if(TARGET CUDA::nppi)
        set(CUDA_nppi_LIBRARY CUDA::nppi)
    endif()
    if(TARGET CUDA::npps)
        set(CUDA_npps_LIBRARY CUDA::npps)
    endif()
    find_package(nvidia-video-codec-sdk QUIET)
    if(nvidia-video-codec-sdk_FOUND)
        set(CUDA_nvencodeapi_LIBRARY nvidia-video-codec-sdk::nvidia-encode)
        set(CUDA_nvcuvid_LIBRARY nvidia-video-codec-sdk::nvcuvid)
    endif()
endif()
