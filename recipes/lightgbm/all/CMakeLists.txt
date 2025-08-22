cmake_minimum_required(VERSION 3.15)
project(cmake_wrapper LANGUAGES CXX)

find_package(Eigen3 REQUIRED CONFIG)
find_package(fast_double_parser REQUIRED CONFIG)
find_package(fmt REQUIRED CONFIG)
if(USE_CUDA)
  find_package(CUDAToolkit REQUIRED)
endif()

# Install headers here instead to avoid having to patch out
# installation of vendored fmt and fast_double_parser.
set(INSTALL_HEADERS OFF)

add_subdirectory(src)

if(_MAJOR_VERSION GREATER_EQUAL 4)
    set(TARGETS lightgbm_objs lightgbm_capi_objs)
    set(VISIBILITY PRIVATE)
else()
    set(TARGETS lightgbm _lightgbm)
    set(VISIBILITY "")
endif()

foreach(target ${TARGETS})
    target_link_libraries(${target} ${VISIBILITY} Eigen3::Eigen fast_double_parser::fast_double_parser fmt::fmt)
    if(USE_CUDA)
      target_link_libraries(${target} ${VISIBILITY} CUDA::cudart)
    endif()
endforeach()

install(
  DIRECTORY src/include/LightGBM
  DESTINATION include
)
