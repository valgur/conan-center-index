cmake_minimum_required(VERSION 3.18)
project(cufftdx_separate_twiddles_lut LANGUAGES CXX CUDA)

find_package(CUDAToolkit REQUIRED)
find_package(NvidiaCutlass REQUIRED)

add_library(cufftdx_separate_twiddles_lut OBJECT src/cufftdx/lut.cu)
target_include_directories(cufftdx_separate_twiddles_lut PUBLIC include/)
target_link_libraries(cufftdx_separate_twiddles_lut PUBLIC CUDA::cuda_driver nvidia::cutlass::cutlass)
set_target_properties(cufftdx_separate_twiddles_lut PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
    CUDA_FATBIN_COMPILATION ON
)
target_compile_definitions(cufftdx_separate_twiddles_lut PUBLIC CUFFTDX_USE_SEPARATE_TWIDDLES)

install(FILES $<TARGET_OBJECTS:cufftdx_separate_twiddles_lut>
    DESTINATION lib
    RENAME libcufftdx_separate_twiddles_lut.fatbin
)
