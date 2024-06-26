# Custom find_package() wrapper because CMakeDeps does not support upper-case CMake var output expected by the project.
macro(custom_find_package name)
    find_package(${name} ${ARGN} REQUIRED)
    string(TOUPPER ${name} name_upper)
    set(${name_upper}_FOUND TRUE)
    set(${name_upper}_VERSION_STRING ${${name}_VERSION_STRING})
    set(${name_upper}_INCLUDE_DIRS ${${name}_INCLUDE_DIRS})
    set(${name_upper}_INCLUDE_DIR ${${name}_INCLUDE_DIR})
    set(${name_upper}_LIBRARIES ${${name}_LIBRARIES})
    set(${name_upper}_DEFINITIONS ${${name}_DEFINITIONS})
    set(${name_upper}_LIBRARY ${${name}_LIBRARIES})
    set(${name}_LIBRARY ${${name}_LIBRARIES})
    set(${name_upper}_INCLUDE_DIR_HINTS "")
    set(${name}_INCLUDE_DIR_HINTS "")
    unset(name_upper)
endmacro()

custom_find_package(cereal REQUIRED CONFIG)
custom_find_package(Ceres REQUIRED)
custom_find_package(Clp REQUIRED)
custom_find_package(CoinUtils REQUIRED)
custom_find_package(Eigen3 REQUIRED)
custom_find_package(Flann REQUIRED CONFIG)
custom_find_package(JPEG REQUIRED)
custom_find_package(Lemon REQUIRED)
custom_find_package(Osi REQUIRED)
custom_find_package(PNG REQUIRED)
custom_find_package(TIFF REQUIRED)

# Don't link against the optional CUDA kernels lib
set(CERES_LIBRARIES Ceres::ceres)
