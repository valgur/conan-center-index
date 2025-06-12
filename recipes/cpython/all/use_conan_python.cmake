if (DEFINED Python3_VERSION_STRING)
    set(_CONAN_PYTHON_SUFFIX "3")
else()
    set(_CONAN_PYTHON_SUFFIX "")
endif()
get_filename_component(_PREFIX_PATH "@PREFIX_PATH@" ABSOLUTE)
# Allow Python_EXECUTABLE to be overridden for cross-compilation support
if(NOT DEFINED Python_EXECUTABLE)
    set(Python${_CONAN_PYTHON_SUFFIX}_EXECUTABLE @PYTHON_EXECUTABLE@)
endif()
set(Python${_CONAN_PYTHON_SUFFIX}_LIBRARY @PYTHON_LIBRARY@)

# Fails if these are set beforehand
unset(Python${_CONAN_PYTHON_SUFFIX}_INCLUDE_DIRS)
unset(Python${_CONAN_PYTHON_SUFFIX}_INCLUDE_DIR)

include(${CMAKE_ROOT}/Modules/FindPython${_CONAN_PYTHON_SUFFIX}.cmake)

# Sanity check: The former comes from FindPython(3), the latter comes from the injected find module
if(NOT Python${_CONAN_PYTHON_SUFFIX}_VERSION VERSION_EQUAL Python${_CONAN_PYTHON_SUFFIX}_VERSION_STRING)
    message(FATAL_ERROR "CMake detected wrong cpython version - this is likely a bug with the cpython Conan package")
endif()

if (TARGET Python${_CONAN_PYTHON_SUFFIX}::Module)
    set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::Module PROPERTIES INTERFACE_LINK_LIBRARIES cpython::python)
endif()
if (TARGET Python${_CONAN_PYTHON_SUFFIX}::SABIModule)
    set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::SABIModule PROPERTIES INTERFACE_LINK_LIBRARIES cpython::python)
endif()
if (TARGET Python${_CONAN_PYTHON_SUFFIX}::Python)
    set_target_properties(Python${_CONAN_PYTHON_SUFFIX}::Python PROPERTIES INTERFACE_LINK_LIBRARIES cpython::embed)
endif()
