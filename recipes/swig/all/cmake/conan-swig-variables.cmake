find_program(SWIG_EXECUTABLE swig)
if(NOT DEFINED SWIG_DIR)
    get_filename_component(_SWIG_DIR ${SWIG_EXECUTABLE}/../swiglib ABSOLUTE)
    set(SWIG_DIR ${_SWIG_DIR} CACHE STRING "Location of SWIG library")
endif()
mark_as_advanced(SWIG_DIR SWIG_EXECUTABLE)
