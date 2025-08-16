#   James Bigler, NVIDIA Corp (nvidia.com - jbigler)
#   Abe Stephens, SCI Institute -- http://www.sci.utah.edu/~abe/FindCuda.html
#
#   Copyright (c) 2008 - 2009 NVIDIA Corporation.  All rights reserved.
#
#   Copyright (c) 2007-2009
#   Scientific Computing and Imaging Institute, University of Utah
#
#   This code is licensed under the MIT License.
#
# The MIT License
#
# License for the specific language governing rights and limitations under
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
###############################################################################

# A modified copy of https://github.com/Kitware/CMake/blob/v4.1.0/Modules/FindCUDA.cmake
# Simplified under the assumption that NVCC and all CUDA Toolkit libraries are provied by Conan.
# Logic that is no longer applicable to CUDA 11.0+ has been dropped.

if(NOT CMAKE_FIND_PACKAGE_NAME STREQUAL "CUDA")
    return()
endif()
include_guard()

set(_conan_cuda_packages
    cudart cuda-crt CCCL libcudacxx Thrust cub nvml-stubs
    cupti cufft cublas cusparse cusolver curand cuda-opencl npp
    nvidia-video-codec-sdk
)

if(CMAKE_GENERATOR MATCHES "Visual Studio")
  cmake_policy(GET CMP0147 _FindCUDA_CMP0147)
  if(_FindCUDA_CMP0147 STREQUAL "NEW")
    message(FATAL_ERROR "The FindCUDA module does not work in Visual Studio with policy CMP0147.")
  endif()
endif()

set(CUDA_VERSION "@CUDA_VERSION@")
set(CUDA_VERSION_STRING "@CUDA_VERSION@")
set(CUDA_VERSION_MAJOR "@CUDA_VERSION_MAJOR@")
set(CUDA_VERSION_MINOR "@CUDA_VERSION_MINOR@")
set(CUDA_FOUND 1)

#####################################################################
## CUDA_INCLUDE_NVCC_DEPENDENCIES
##

macro(CUDA_INCLUDE_NVCC_DEPENDENCIES dependency_file)
  set(CUDA_NVCC_DEPEND)
  set(CUDA_NVCC_DEPEND_REGENERATE FALSE)
  if(NOT EXISTS ${dependency_file})
    file(WRITE ${dependency_file} "#FindCUDA.cmake generated file.  Do not edit.\n")
  endif()
  include(${dependency_file})
  if(CUDA_NVCC_DEPEND)
    foreach(f ${CUDA_NVCC_DEPEND})
      if(NOT EXISTS ${f})
        set(CUDA_NVCC_DEPEND_REGENERATE TRUE)
      endif()
    endforeach()
  else()
    set(CUDA_NVCC_DEPEND_REGENERATE TRUE)
  endif()
  if(CUDA_NVCC_DEPEND_REGENERATE)
    set(CUDA_NVCC_DEPEND ${dependency_file})
    file(WRITE ${dependency_file} "#FindCUDA.cmake generated file.  Do not edit.\n")
  endif()
endmacro()

###############################################################################
###############################################################################
# Setup variables' defaults
###############################################################################
###############################################################################

option(CUDA_ATTACH_VS_BUILD_RULE_TO_CUDA_FILE "Attach the build rule to the CUDA source file.  Enable only when the CUDA source file is added to at most one target." ON)
option(CUDA_BUILD_CUBIN "Generate and parse .cubin files in Device mode." OFF)
set(CUDA_GENERATED_OUTPUT_DIR "" CACHE PATH "Directory to put all the output files.  If blank it will default to the CMAKE_CURRENT_BINARY_DIR")

cmake_initialize_per_config_variable(CUDA_NVCC_FLAGS "Semi-colon delimit multiple arguments.")

if(DEFINED ENV{CUDAHOSTCXX})
  set(CUDA_HOST_COMPILER "$ENV{CUDAHOSTCXX}" CACHE FILEPATH "Host side compiler used by NVCC")
elseif(CMAKE_GENERATOR MATCHES "Visual Studio")
  set(_CUDA_MSVC_HOST_COMPILER "$(VCInstallDir)Tools/MSVC/$(VCToolsVersion)/bin/Host$(Platform)/$(PlatformTarget)")
  if(MSVC_VERSION LESS 1910)
    set(_CUDA_MSVC_HOST_COMPILER "$(VCInstallDir)bin")
  endif()
  set(CUDA_HOST_COMPILER "${_CUDA_MSVC_HOST_COMPILER}" CACHE FILEPATH "Host side compiler used by NVCC")
# elseif(NOT CUDA_HOST_COMPILER)
#   message(WARNING "Could not detemine CUDA_HOST_COMPILER. Please set it manually or set the CUDAHOSTCXX environment variable.")
endif()

option(CUDA_PROPAGATE_HOST_FLAGS "Propagate CXX_FLAGS and friends to the host compiler via -Xcompile" ON)
option(CUDA_SEPARABLE_COMPILATION "Compile CUDA objects with separable compilation enabled." OFF)
option(CUDA_VERBOSE_BUILD "Print out the commands run while compiling the CUDA source file.  With the Makefile generator this defaults to VERBOSE variable specified on the command line, but can be forced on with this option." OFF)

mark_as_advanced(
  CUDA_ATTACH_VS_BUILD_RULE_TO_CUDA_FILE
  CUDA_GENERATED_OUTPUT_DIR
  CUDA_NVCC_FLAGS
  CUDA_PROPAGATE_HOST_FLAGS
  CUDA_BUILD_CUBIN
  CUDA_VERBOSE_BUILD
  CUDA_SEPARABLE_COMPILATION
  )

set(CUDA_configuration_types ${CMAKE_CONFIGURATION_TYPES} ${CMAKE_BUILD_TYPE} Debug MinSizeRel Release RelWithDebInfo)
list(REMOVE_DUPLICATES CUDA_configuration_types)

###############################################################################
###############################################################################
# Locate CUDA, Set Build Type, etc.
###############################################################################
###############################################################################


foreach(pkg ${_conan_cuda_packages})
    find_package(${pkg} QUIET)
    if(NOT ${pkg}_FOUND)
        continue()
    endif()
    list(APPEND CUDA_INCLUDE_DIRS ${${pkg}_INCLUDE_DIRS})
    list(APPEND CUDA_LIBRARIES ${${pkg}_LIBARIES})  # Not an official variable
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib" ABSOLUTE)
        list(APPEND CUDA_LIBRARY_DIR "${_lib_dir}")
    endif()
    if(EXISTS "${${pkg}_INCLUDE_DIR}/../lib/stubs")
        get_filename_component(_lib_dir "${${pkg}_INCLUDE_DIR}/../lib/stubs" ABSOLUTE)
        list(APPEND CUDA_LIBRARY_DIR "${_lib_dir}")
    endif()
endforeach()

find_program(CUDA_NVCC_EXECUTABLE nvcc QUIET)
if(CUDA_NVCC_EXECUTABLE)
    execute_process(COMMAND ${CUDA_NVCC_EXECUTABLE} --version OUTPUT_VARIABLE _nvcc_version_output)
    if("${_nvcc_version_output}" MATCHES "release ([0-9]+\\.[0-9]+)," AND
       CMAKE_MATCH_1 STREQUAL "${CUDA_VERSION}")
        get_filename_component(CUDA_BIN_DIR "${CUDA_NVCC_EXECUTABLE}" DIRECTORY)
        get_filename_component(CUDA_TOOLKIT_ROOT_DIR "${CUDA_BIN_DIR}" DIRECTORY)
        set(CUDA_TARGET_DIR "${CUDA_TOOLKIT_ROOT_DIR}")
        set(CUDA_LIBRARY_ROOT "${CUDA_TOOLKIT_ROOT_DIR}/lib")
    else()
        if(NOT CUDA_FIND_QUIETLY)
            message(WARNING "Found NVCC at ${CUDA_NVCC_EXECUTABLE},"
                            " but its version '${CMAKE_MATCH_1}' did not match CUDA version of '${CUDA_VERSION}'.")
        endif()
        set(CUDA_NVCC_EXECUTABLE "")
    endif()
endif()

set(CUDA_SDK_ROOT_DIR "${CUDA_TOOLKIT_ROOT_DIR}")
set(CUDA_TOOLKIT_INCLUDE "${CUDA_INCLUDE_DIRS}")
set(CUDA_HAS_FP16 TRUE)

# Set the user list of include dir to nothing to initialize it.
set(CUDA_NVCC_INCLUDE_DIRS_USER "")
set(CUDA_INCLUDE_DIRS ${CUDA_TOOLKIT_INCLUDE})

macro(_set_cuda_library_vars _name _lib_name)
  string(TOUPPER ${_name} _name_upper)
  set(CUDA_${_name}_LIBRARY ${_lib_name})
  set(CUDA_${_name}_LIBRARIES ${_lib_name})
  set(CUDA_${_name_upper}_LIBRARY ${_lib_name})
  set(CUDA_${_name_upper}_LIBRARIES ${_lib_name})
endmacro()

if(TARGET CUDA::cufft)
  _set_cuda_library_vars(cufft CUDA::cufft)
endif()
if(TARGET CUDA::cublas)
  _set_cuda_library_vars(cublas CUDA::cublas)
endif()
if(TARGET CUDA::cudart)
  _set_cuda_library_vars(cudart CUDA::cudart)
endif()
if(TARGET CUDA::cudart_static)
  _set_cuda_library_vars(cudart_static CUDA::cudart_static)
endif()
if(TARGET CUDA::cupti)
  _set_cuda_library_vars(cupti CUDA::cupti)
endif()
if(TARGET CUDA::curand)
  _set_cuda_library_vars(curand CUDA::curand)
endif()
if(TARGET CUDA::cudadevrt)
  _set_cuda_library_vars(cudadevrt CUDA::cudadevrt)
endif()
if(TARGET CUDA::cusolver)
  _set_cuda_library_vars(cusolver CUDA::cusolver)
endif()
if(TARGET CUDA::cusparse)
  _set_cuda_library_vars(cusparse CUDA::cusparse)
endif()
foreach(npp_lib npp nppc nppi nppial nppicc nppicom nppidei nppif nppig nppim nppist nppisu nppitc npps)
  if(TARGET npp::${npp_lib})
    _set_cuda_library_vars(${npp_lib} npp::${npp_lib})
  endif()
endforeach()
if(nvidia-video-codec-sdk_FOUND)
  _set_cuda_library_vars(nvencodeapi nvidia-video-codec-sdk::nvidia-encode)
  _set_cuda_library_vars(nvcuvid nvidia-video-codec-sdk::nvcuvid)
endif()
if(TARGET CUDA::OpenCL)
  _set_cuda_library_vars(OpenCL CUDA::OpenCL)
endif()

###############################################################################
###############################################################################
# Macros
###############################################################################
###############################################################################

###############################################################################
# Add include directories to pass to the nvcc command.
macro(CUDA_INCLUDE_DIRECTORIES)
  foreach(dir ${ARGN})
    list(APPEND CUDA_NVCC_INCLUDE_DIRS_USER ${dir})
  endforeach()
endmacro()


##############################################################################
macro(CUDA_FIND_HELPER_FILE _name _extension)
  set(_full_name "${_name}.${_extension}")
  get_filename_component(CMAKE_CURRENT_LIST_DIR "${CMAKE_CURRENT_LIST_FILE}" PATH)
  set(CUDA_${_name} "${CMAKE_CURRENT_LIST_DIR}/${_full_name}")
  set(CUDA_${_name} ${CUDA_${_name}} CACHE INTERNAL "Location of ${_full_name}" FORCE)
endmacro()

cuda_find_helper_file(parse_cubin cmake)
cuda_find_helper_file(make2cmake cmake)
cuda_find_helper_file(run_nvcc cmake)
# include("${CMAKE_CURRENT_LIST_DIR}/FindCUDA/select_compute_arch.cmake")

# Mock implementation, since the cuda.architectures setting together with NvccToolchain should be used instead.
macro(cuda_select_nvcc_arch_flags _var)
  set(${_var} "")
endmacro()

##############################################################################
# Separate the OPTIONS out from the sources
#
macro(CUDA_GET_SOURCES_AND_OPTIONS _sources _cmake_options _options)
  set( ${_sources} )
  set( ${_cmake_options} )
  set( ${_options} )
  set( _found_options FALSE )
  foreach(arg ${ARGN})
    if("x${arg}" STREQUAL "xOPTIONS")
      set( _found_options TRUE )
    elseif(
        "x${arg}" STREQUAL "xWIN32" OR
        "x${arg}" STREQUAL "xMACOSX_BUNDLE" OR
        "x${arg}" STREQUAL "xEXCLUDE_FROM_ALL" OR
        "x${arg}" STREQUAL "xSTATIC" OR
        "x${arg}" STREQUAL "xSHARED" OR
        "x${arg}" STREQUAL "xMODULE"
        )
      list(APPEND ${_cmake_options} ${arg})
    else()
      if ( _found_options )
        list(APPEND ${_options} ${arg})
      else()
        # Assume this is a file
        list(APPEND ${_sources} ${arg})
      endif()
    endif()
  endforeach()
endmacro()

##############################################################################
# Parse the OPTIONS from ARGN and set the variables prefixed by _option_prefix
#
macro(CUDA_PARSE_NVCC_OPTIONS _option_prefix)
  set( _found_config )
  foreach(arg ${ARGN})
    # Determine if we are dealing with a perconfiguration flag
    foreach(config ${CUDA_configuration_types})
      string(TOUPPER ${config} config_upper)
      if (arg STREQUAL "${config_upper}")
        set( _found_config _${arg})
        # Set arg to nothing to keep it from being processed further
        set( arg )
      endif()
    endforeach()

    if ( arg )
      list(APPEND ${_option_prefix}${_found_config} "${arg}")
    endif()
  endforeach()
endmacro()

##############################################################################
# Helper to add the include directory for CUDA only once
function(CUDA_ADD_CUDA_INCLUDE_ONCE)
  get_directory_property(_include_directories INCLUDE_DIRECTORIES)
  set(_add TRUE)
  if(_include_directories)
    foreach(dir ${_include_directories})
      if("${dir}" STREQUAL "${CUDA_INCLUDE_DIRS}")
        set(_add FALSE)
      endif()
    endforeach()
  endif()
  if(_add)
    include_directories(${CUDA_INCLUDE_DIRS})
  endif()
endfunction()

function(CUDA_BUILD_SHARED_LIBRARY shared_flag)
  set(cmake_args ${ARGN})
  # If SHARED, MODULE, or STATIC aren't already in the list of arguments, then
  # add SHARED or STATIC based on the value of BUILD_SHARED_LIBS.
  list(FIND cmake_args SHARED _cuda_found_SHARED)
  list(FIND cmake_args MODULE _cuda_found_MODULE)
  list(FIND cmake_args STATIC _cuda_found_STATIC)
  if( _cuda_found_SHARED GREATER -1 OR
      _cuda_found_MODULE GREATER -1 OR
      _cuda_found_STATIC GREATER -1)
    set(_cuda_build_shared_libs)
  else()
    if (BUILD_SHARED_LIBS)
      set(_cuda_build_shared_libs SHARED)
    else()
      set(_cuda_build_shared_libs STATIC)
    endif()
  endif()
  set(${shared_flag} ${_cuda_build_shared_libs} PARENT_SCOPE)
endfunction()

##############################################################################
# Helper to avoid clashes of files with the same basename but different paths.
# This doesn't attempt to do exactly what CMake internals do, which is to only
# add this path when there is a conflict, since by the time a second collision
# in names is detected it's already too late to fix the first one.  For
# consistency sake the relative path will be added to all files.
function(CUDA_COMPUTE_BUILD_PATH path build_path)
  #message("CUDA_COMPUTE_BUILD_PATH([${path}] ${build_path})")
  # Only deal with CMake style paths from here on out
  file(TO_CMAKE_PATH "${path}" bpath)
  if (IS_ABSOLUTE "${bpath}")
    # Absolute paths are generally unnecessary, especially if something like
    # file(GLOB_RECURSE) is used to pick up the files.

    string(FIND "${bpath}" "${CMAKE_CURRENT_BINARY_DIR}" _binary_dir_pos)
    if (_binary_dir_pos EQUAL 0)
      file(RELATIVE_PATH bpath "${CMAKE_CURRENT_BINARY_DIR}" "${bpath}")
    else()
      file(RELATIVE_PATH bpath "${CMAKE_CURRENT_SOURCE_DIR}" "${bpath}")
    endif()
  endif()

  # This recipe is from cmLocalGenerator::CreateSafeUniqueObjectFileName in the
  # CMake source.

  # Remove leading /
  string(REGEX REPLACE "^[/]+" "" bpath "${bpath}")
  # Avoid absolute paths by removing ':'
  string(REPLACE ":" "_" bpath "${bpath}")
  # Avoid relative paths that go up the tree
  string(REPLACE "../" "__/" bpath "${bpath}")
  # Avoid spaces
  string(REPLACE " " "_" bpath "${bpath}")

  # Strip off the filename.  I wait until here to do it, since removing the
  # basename can make a path that looked like path/../basename turn into
  # path/.. (notice the trailing slash).
  get_filename_component(bpath "${bpath}" PATH)

  set(${build_path} "${bpath}" PARENT_SCOPE)
  #message("${build_path} = ${bpath}")
endfunction()

##############################################################################
# This helper macro populates the following variables and setups up custom
# commands and targets to invoke the nvcc compiler to generate C or PTX source
# dependent upon the format parameter.  The compiler is invoked once with -M
# to generate a dependency file and a second time with -cuda or -ptx to generate
# a .cpp or .ptx file.
# INPUT:
#   cuda_target         - Target name
#   format              - PTX, CUBIN, FATBIN or OBJ
#   FILE1 .. FILEN      - The remaining arguments are the sources to be wrapped.
#   OPTIONS             - Extra options to NVCC
# OUTPUT:
#   generated_files     - List of generated files
##############################################################################
##############################################################################

macro(CUDA_WRAP_SRCS cuda_target format generated_files)

  # Put optional arguments in list.
  set(_argn_list "${ARGN}")
  # If one of the given optional arguments is "PHONY", make a note of it, then
  # remove it from the list.
  list(FIND _argn_list "PHONY" _phony_idx)
  if("${_phony_idx}" GREATER "-1")
    set(_target_is_phony true)
    list(REMOVE_AT _argn_list ${_phony_idx})
  else()
    set(_target_is_phony false)
  endif()

  # If CMake doesn't support separable compilation, complain
  if(CUDA_SEPARABLE_COMPILATION AND CMAKE_VERSION VERSION_LESS "2.8.10.1")
    message(SEND_ERROR "CUDA_SEPARABLE_COMPILATION isn't supported for CMake versions less than 2.8.10.1")
  endif()

  # Set up all the command line flags here, so that they can be overridden on a per target basis.

  set(nvcc_flags "")

  set(generated_extension ${CMAKE_CXX_OUTPUT_EXTENSION})

  # This needs to be passed in at this stage, because VS needs to fill out the
  # various macros from within VS.  Note that CCBIN is only used if
  # -ccbin or --compiler-bindir isn't used and CUDA_HOST_COMPILER matches
  # _CUDA_MSVC_HOST_COMPILER
  if(CMAKE_GENERATOR MATCHES "Visual Studio")
    set(ccbin_flags -D "\"CCBIN:PATH=${_CUDA_MSVC_HOST_COMPILER}\"" )
  else()
    set(ccbin_flags)
  endif()

  # Figure out which configure we will use and pass that in as an argument to
  # the script.  We need to defer the decision until compilation time, because
  # for VS projects we won't know if we are making a debug or release build
  # until build time.
  if(CMAKE_GENERATOR MATCHES "Visual Studio")
    set( CUDA_build_configuration "$(ConfigurationName)" )
  else()
    set( CUDA_build_configuration "${CMAKE_BUILD_TYPE}")
  endif()

  # Initialize our list of includes with the user ones followed by the CUDA system ones.
  set(CUDA_NVCC_INCLUDE_DIRS ${CUDA_NVCC_INCLUDE_DIRS_USER} "${CUDA_INCLUDE_DIRS}")
  if(_target_is_phony)
    # If the passed in target name isn't a real target (i.e., this is from a call to one of the
    # cuda_compile_* functions), need to query directory properties to get include directories
    # and compile definitions.
    get_directory_property(_dir_include_dirs INCLUDE_DIRECTORIES)
    get_directory_property(_dir_compile_defs COMPILE_DEFINITIONS)

    list(APPEND CUDA_NVCC_INCLUDE_DIRS "${_dir_include_dirs}")
    set(CUDA_NVCC_COMPILE_DEFINITIONS "${_dir_compile_defs}")
  else()
    # Append the include directories for this target via generator expression, which is
    # expanded by the file(GENERATE) call below.  This generator expression captures all
    # include dirs set by the user, whether via directory properties or target properties
    list(APPEND CUDA_NVCC_INCLUDE_DIRS "$<TARGET_PROPERTY:${cuda_target},INCLUDE_DIRECTORIES>")

    # Do the same thing with compile definitions
    set(CUDA_NVCC_COMPILE_DEFINITIONS "$<TARGET_PROPERTY:${cuda_target},COMPILE_DEFINITIONS>")
  endif()


  # Reset these variables
  set(CUDA_WRAP_OPTION_NVCC_FLAGS)
  foreach(config ${CUDA_configuration_types})
    string(TOUPPER ${config} config_upper)
    set(CUDA_WRAP_OPTION_NVCC_FLAGS_${config_upper})
  endforeach()

  CUDA_GET_SOURCES_AND_OPTIONS(_cuda_wrap_sources _cuda_wrap_cmake_options _cuda_wrap_options ${_argn_list})
  CUDA_PARSE_NVCC_OPTIONS(CUDA_WRAP_OPTION_NVCC_FLAGS ${_cuda_wrap_options})

  # Figure out if we are building a shared library.  BUILD_SHARED_LIBS is
  # respected in CUDA_ADD_LIBRARY.
  set(_cuda_build_shared_libs FALSE)
  # SHARED, MODULE
  list(FIND _cuda_wrap_cmake_options SHARED _cuda_found_SHARED)
  list(FIND _cuda_wrap_cmake_options MODULE _cuda_found_MODULE)
  if(_cuda_found_SHARED GREATER -1 OR _cuda_found_MODULE GREATER -1)
    set(_cuda_build_shared_libs TRUE)
  endif()
  # STATIC
  list(FIND _cuda_wrap_cmake_options STATIC _cuda_found_STATIC)
  if(_cuda_found_STATIC GREATER -1)
    set(_cuda_build_shared_libs FALSE)
  endif()

  # CUDA_HOST_FLAGS
  if(_cuda_build_shared_libs)
    # If we are setting up code for a shared library, then we need to add extra flags for
    # compiling objects for shared libraries.
    set(CUDA_HOST_SHARED_FLAGS ${CMAKE_SHARED_LIBRARY_CXX_FLAGS})
  else()
    set(CUDA_HOST_SHARED_FLAGS)
  endif()
  # Only add the CMAKE_{C,CXX}_FLAGS if we are propagating host flags.  We
  # always need to set the SHARED_FLAGS, though.
  if(CUDA_PROPAGATE_HOST_FLAGS)
    set(_cuda_host_flags "set(CMAKE_HOST_FLAGS ${CMAKE_CXX_FLAGS} ${CUDA_HOST_SHARED_FLAGS})")
  else()
    set(_cuda_host_flags "set(CMAKE_HOST_FLAGS ${CUDA_HOST_SHARED_FLAGS})")
  endif()

  set(_cuda_nvcc_flags_config "# Build specific configuration flags")
  # Loop over all the configuration types to generate appropriate flags for run_nvcc.cmake
  foreach(config ${CUDA_configuration_types})
    string(TOUPPER ${config} config_upper)
    # CMAKE_FLAGS are strings and not lists.  By not putting quotes around CMAKE_FLAGS
    # we convert the strings to lists (like we want).

    if(CUDA_PROPAGATE_HOST_FLAGS)
      # nvcc chokes on -g3 in versions previous to 3.0, so replace it with -g
      set(_cuda_fix_g3 FALSE)

      if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
        if (CUDA_VERSION VERSION_LESS  "3.0" OR
            CUDA_VERSION VERSION_EQUAL "4.1" OR
            CUDA_VERSION VERSION_EQUAL "4.2"
            )
          set(_cuda_fix_g3 TRUE)
        endif()
      endif()
      if(_cuda_fix_g3)
        string(REPLACE "-g3" "-g" _cuda_C_FLAGS "${CMAKE_CXX_FLAGS_${config_upper}}")
      else()
        set(_cuda_C_FLAGS "${CMAKE_CXX_FLAGS_${config_upper}}")
      endif()

      string(APPEND _cuda_host_flags "\nset(CMAKE_HOST_FLAGS_${config_upper} ${_cuda_C_FLAGS})")
    endif()

    # Note that if we ever want CUDA_NVCC_FLAGS_<CONFIG> to be string (instead of a list
    # like it is currently), we can remove the quotes around the
    # ${CUDA_NVCC_FLAGS_${config_upper}} variable like the CMAKE_HOST_FLAGS_<CONFIG> variable.
    string(APPEND _cuda_nvcc_flags_config "\nset(CUDA_NVCC_FLAGS_${config_upper} ${CUDA_NVCC_FLAGS_${config_upper}} ;; ${CUDA_WRAP_OPTION_NVCC_FLAGS_${config_upper}})")
  endforeach()

  # Process the C++11 flag.  If the host sets the flag, we need to add it to nvcc and
  # remove it from the host. This is because -Xcompile -std=c++ will choke nvcc (it uses
  # the C preprocessor).  In order to get this to work correctly, we need to use nvcc's
  # specific c++11 flag.
  if( "${_cuda_host_flags}" MATCHES "-std=c\\+\\+11")
    # Add the c++11 flag to nvcc if it isn't already present.  Note that we only look at
    # the main flag instead of the configuration specific flags.
    if( NOT "${CUDA_NVCC_FLAGS}" MATCHES "-std=c\\+\\+11" )
      list(APPEND nvcc_flags --std c++11)
    endif()
    string(REGEX REPLACE "[-]+std=c\\+\\+11" "" _cuda_host_flags "${_cuda_host_flags}")
  endif()

  if(_cuda_build_shared_libs)
    list(APPEND nvcc_flags "-D${cuda_target}_EXPORTS")
  endif()

  # Reset the output variable
  set(_cuda_wrap_generated_files "")

  # Iterate over the macro arguments and create custom
  # commands for all the .cu files.
  foreach(file ${_argn_list})
    # Ignore any file marked as a HEADER_FILE_ONLY
    get_source_file_property(_is_header ${file} HEADER_FILE_ONLY)
    # Allow per source file overrides of the format.  Also allows compiling non-.cu files.
    get_source_file_property(_cuda_source_format ${file} CUDA_SOURCE_PROPERTY_FORMAT)
    if((${file} MATCHES "\\.cu$" OR _cuda_source_format) AND NOT _is_header)

      if(NOT _cuda_source_format)
        set(_cuda_source_format ${format})
      endif()
      # If file isn't a .cu file, we need to tell nvcc to treat it as such.
      if(NOT ${file} MATCHES "\\.cu$")
        set(cuda_language_flag -x=cu)
      else()
        set(cuda_language_flag)
      endif()

      if( ${_cuda_source_format} MATCHES "OBJ")
        set( cuda_compile_to_external_module OFF )
      else()
        set( cuda_compile_to_external_module ON )
        if( ${_cuda_source_format} MATCHES "PTX" )
          set( cuda_compile_to_external_module_type "ptx" )
        elseif( ${_cuda_source_format} MATCHES "CUBIN")
          set( cuda_compile_to_external_module_type "cubin" )
        elseif( ${_cuda_source_format} MATCHES "FATBIN")
          set( cuda_compile_to_external_module_type "fatbin" )
        else()
          message( FATAL_ERROR "Invalid format flag passed to CUDA_WRAP_SRCS or set with CUDA_SOURCE_PROPERTY_FORMAT file property for file '${file}': '${_cuda_source_format}'.  Use OBJ, PTX, CUBIN or FATBIN.")
        endif()
      endif()

      if(cuda_compile_to_external_module)
        # Don't use any of the host compilation flags for PTX targets.
        set(CUDA_HOST_FLAGS)
        set(CUDA_NVCC_FLAGS_CONFIG)
      else()
        set(CUDA_HOST_FLAGS ${_cuda_host_flags})
        set(CUDA_NVCC_FLAGS_CONFIG ${_cuda_nvcc_flags_config})
      endif()

      # Determine output directory
      cuda_compute_build_path("${file}" cuda_build_path)
      set(cuda_compile_intermediate_directory "${CMAKE_CURRENT_BINARY_DIR}/CMakeFiles/${cuda_target}.dir/${cuda_build_path}")
      if(CUDA_GENERATED_OUTPUT_DIR)
        set(cuda_compile_output_dir "${CUDA_GENERATED_OUTPUT_DIR}")
      else()
        if ( cuda_compile_to_external_module )
          set(cuda_compile_output_dir "${CMAKE_CURRENT_BINARY_DIR}")
        else()
          set(cuda_compile_output_dir "${cuda_compile_intermediate_directory}")
        endif()
      endif()

      # Add a custom target to generate a c or ptx file. ######################

      get_filename_component( basename ${file} NAME )
      if( cuda_compile_to_external_module )
        set(generated_file_path "${cuda_compile_output_dir}")
        set(generated_file_basename "${cuda_target}_generated_${basename}.${cuda_compile_to_external_module_type}")
        set(format_flag "-${cuda_compile_to_external_module_type}")
        file(MAKE_DIRECTORY "${cuda_compile_output_dir}")
      else()
        set(generated_file_path "${cuda_compile_output_dir}/${CMAKE_CFG_INTDIR}")
        set(generated_file_basename "${cuda_target}_generated_${basename}${generated_extension}")
        if(CUDA_SEPARABLE_COMPILATION)
          set(format_flag "-dc")
        else()
          set(format_flag "-c")
        endif()
      endif()

      # Set all of our file names.  Make sure that whatever filenames that have
      # generated_file_path in them get passed in through as a command line
      # argument, so that the ${CMAKE_CFG_INTDIR} gets expanded at run time
      # instead of configure time.
      set(generated_file "${generated_file_path}/${generated_file_basename}")
      set(cmake_dependency_file "${cuda_compile_intermediate_directory}/${generated_file_basename}.depend")
      set(NVCC_generated_dependency_file "${cuda_compile_intermediate_directory}/${generated_file_basename}.NVCC-depend")
      set(generated_cubin_file "${generated_file_path}/${generated_file_basename}.cubin.txt")
      set(custom_target_script_pregen "${cuda_compile_intermediate_directory}/${generated_file_basename}.cmake.pre-gen")
      set(custom_target_script "${cuda_compile_intermediate_directory}/${generated_file_basename}$<$<BOOL:$<CONFIG>>:.$<CONFIG>>.cmake")

      # Setup properties for obj files:
      if( NOT cuda_compile_to_external_module )
        set_source_files_properties("${generated_file}"
          PROPERTIES
          EXTERNAL_OBJECT true # This is an object file not to be compiled, but only be linked.
          )
      endif()

      # Don't add CMAKE_CURRENT_SOURCE_DIR if the path is already an absolute path.
      get_filename_component(file_path "${file}" PATH)
      if(IS_ABSOLUTE "${file_path}")
        set(source_file "${file}")
      else()
        set(source_file "${CMAKE_CURRENT_SOURCE_DIR}/${file}")
      endif()

      if( NOT cuda_compile_to_external_module AND CUDA_SEPARABLE_COMPILATION)
        list(APPEND ${cuda_target}_SEPARABLE_COMPILATION_OBJECTS "${generated_file}")
      endif()

      # Bring in the dependencies.  Creates a variable CUDA_NVCC_DEPEND #######
      cuda_include_nvcc_dependencies(${cmake_dependency_file})

      # Convenience string for output #########################################
      set(cuda_build_type "Device")

      # Build the NVCC made dependency file ###################################
      set(build_cubin OFF)
      if ( CUDA_BUILD_CUBIN )
         if ( NOT cuda_compile_to_external_module )
           set ( build_cubin ON )
         endif()
      endif()

      # Configure the build script
      configure_file("${CUDA_run_nvcc}" "${custom_target_script_pregen}" @ONLY)
      file(GENERATE
        OUTPUT "${custom_target_script}"
        INPUT "${custom_target_script_pregen}"
        )

      # So if a user specifies the same cuda file as input more than once, you
      # can have bad things happen with dependencies.  Here we check an option
      # to see if this is the behavior they want.
      if(CUDA_ATTACH_VS_BUILD_RULE_TO_CUDA_FILE)
        set(main_dep MAIN_DEPENDENCY ${source_file})
      else()
        set(main_dep DEPENDS ${source_file})
      endif()

      if(CUDA_VERBOSE_BUILD)
        set(verbose_output ON)
      elseif(CMAKE_GENERATOR MATCHES "Makefiles")
        set(verbose_output "$(VERBOSE)")
      else()
        set(verbose_output OFF)
      endif()

      # Create up the comment string
      file(RELATIVE_PATH generated_file_relative_path "${CMAKE_BINARY_DIR}" "${generated_file}")
      if(cuda_compile_to_external_module)
        set(cuda_build_comment_string "Building NVCC ${cuda_compile_to_external_module_type} file ${generated_file_relative_path}")
      else()
        set(cuda_build_comment_string "Building NVCC (${cuda_build_type}) object ${generated_file_relative_path}")
      endif()

      set(_verbatim VERBATIM)
      if(ccbin_flags MATCHES "\\$\\(VCInstallDir\\)")
        set(_verbatim "")
      endif()

      # Build the generated file and dependency file ##########################
      add_custom_command(
        OUTPUT ${generated_file}
        # These output files depend on the source_file and the contents of cmake_dependency_file
        ${main_dep}
        DEPENDS ${CUDA_NVCC_DEPEND}
        DEPENDS ${custom_target_script}
        # Make sure the output directory exists before trying to write to it.
        COMMAND ${CMAKE_COMMAND} -E make_directory "${generated_file_path}"
        COMMAND ${CMAKE_COMMAND} ARGS
          -D verbose:BOOL=${verbose_output}
          ${ccbin_flags}
          -D build_configuration:STRING=${CUDA_build_configuration}
          -D "generated_file:STRING=${generated_file}"
          -D "generated_cubin_file:STRING=${generated_cubin_file}"
          -P "${custom_target_script}"
        WORKING_DIRECTORY "${cuda_compile_intermediate_directory}"
        COMMENT "${cuda_build_comment_string}"
        ${_verbatim}
        )

      # Make sure the build system knows the file is generated.
      set_source_files_properties(${generated_file} PROPERTIES GENERATED TRUE)

      list(APPEND _cuda_wrap_generated_files ${generated_file})

      # Add the other files that we want cmake to clean on a cleanup ##########
      list(APPEND CUDA_ADDITIONAL_CLEAN_FILES "${cmake_dependency_file}")
      list(REMOVE_DUPLICATES CUDA_ADDITIONAL_CLEAN_FILES)
      set(CUDA_ADDITIONAL_CLEAN_FILES ${CUDA_ADDITIONAL_CLEAN_FILES} CACHE INTERNAL "List of intermediate files that are part of the cuda dependency scanning.")

    endif()
  endforeach()

  # Set the return parameter
  set(${generated_files} ${_cuda_wrap_generated_files})
endmacro()

function(_cuda_get_important_host_flags important_flags flag_string)
  if(CMAKE_GENERATOR MATCHES "Visual Studio")
    string(REGEX MATCHALL "/M[DT][d]?" flags "${flag_string}")
    list(APPEND ${important_flags} ${flags})
  else()
    string(REGEX MATCHALL "-fPIC" flags "${flag_string}")
    list(APPEND ${important_flags} ${flags})
  endif()
  set(${important_flags} ${${important_flags}} PARENT_SCOPE)
endfunction()

###############################################################################
###############################################################################
# Separable Compilation Link
###############################################################################
###############################################################################

# Compute the filename to be used by CUDA_LINK_SEPARABLE_COMPILATION_OBJECTS
function(CUDA_COMPUTE_SEPARABLE_COMPILATION_OBJECT_FILE_NAME output_file_var cuda_target object_files)
  if (object_files)
    set(generated_extension ${CMAKE_CXX_OUTPUT_EXTENSION})
    set(output_file "${CMAKE_CURRENT_BINARY_DIR}/CMakeFiles/${cuda_target}.dir/${CMAKE_CFG_INTDIR}/${cuda_target}_intermediate_link${generated_extension}")
  else()
    set(output_file)
  endif()

  set(${output_file_var} "${output_file}" PARENT_SCOPE)
endfunction()

# Setup the build rule for the separable compilation intermediate link file.
function(CUDA_LINK_SEPARABLE_COMPILATION_OBJECTS output_file cuda_target options object_files)
  if (object_files)

    set_source_files_properties("${output_file}"
      PROPERTIES
      EXTERNAL_OBJECT TRUE # This is an object file not to be compiled, but only
                           # be linked.
      GENERATED TRUE       # This file is generated during the build
      )

    # For now we are ignoring all the configuration specific flags.
    set(nvcc_flags)
    CUDA_PARSE_NVCC_OPTIONS(nvcc_flags ${options})

    # Create a list of flags specified by CUDA_NVCC_FLAGS_${CONFIG} and CMAKE_CXX_FLAGS*
    set(config_specific_flags)
    set(flags)
    foreach(config ${CUDA_configuration_types})
      string(TOUPPER ${config} config_upper)
      # Add config specific flags
      foreach(f ${CUDA_NVCC_FLAGS_${config_upper}})
        list(APPEND config_specific_flags $<$<CONFIG:${config}>:${f}>)
      endforeach()
      set(important_host_flags)
      _cuda_get_important_host_flags(important_host_flags ${CMAKE_CXX_FLAGS_${config_upper}})
      foreach(f ${important_host_flags})
        list(APPEND flags $<$<CONFIG:${config}>:-Xcompiler> $<$<CONFIG:${config}>:${f}>)
      endforeach()
    endforeach()
    # Add CMAKE_CXX_FLAGS
    set(important_host_flags)
    _cuda_get_important_host_flags(important_host_flags "${CMAKE_CXX_FLAGS}")
    foreach(f ${important_host_flags})
      list(APPEND flags -Xcompiler ${f})
    endforeach()

    # Add our general CUDA_NVCC_FLAGS with the configuration specific flags
    set(nvcc_flags ${CUDA_NVCC_FLAGS} ${config_specific_flags} ${nvcc_flags})

    file(RELATIVE_PATH output_file_relative_path "${CMAKE_BINARY_DIR}" "${output_file}")

    # Some generators don't handle the multiple levels of custom command
    # dependencies correctly (obj1 depends on file1, obj2 depends on obj1), so
    # we work around that issue by compiling the intermediate link object as a
    # pre-link custom command in that situation.
    set(do_obj_build_rule TRUE)
    if (MSVC_VERSION GREATER 1599 AND MSVC_VERSION LESS 1800)
      # VS 2010 and 2012 have this problem.
      set(do_obj_build_rule FALSE)
    endif()

    set(_verbatim VERBATIM)
    if(nvcc_flags MATCHES "\\$\\(VCInstallDir\\)")
      set(_verbatim "")
    endif()

    if (do_obj_build_rule)
      add_custom_command(
        OUTPUT ${output_file}
        DEPENDS ${object_files}
        COMMAND ${CUDA_NVCC_EXECUTABLE} ${nvcc_flags} -dlink ${object_files} -o ${output_file}
        ${flags}
        COMMENT "Building NVCC intermediate link file ${output_file_relative_path}"
        COMMAND_EXPAND_LISTS
        ${_verbatim}
        )
    else()
      get_filename_component(output_file_dir "${output_file}" DIRECTORY)
      add_custom_command(
        TARGET ${cuda_target}
        PRE_LINK
        COMMAND ${CMAKE_COMMAND} -E echo "Building NVCC intermediate link file ${output_file_relative_path}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${output_file_dir}"
        COMMAND ${CUDA_NVCC_EXECUTABLE} ${nvcc_flags} ${flags} -dlink ${object_files} -o "${output_file}"
        COMMAND_EXPAND_LISTS
        ${_verbatim}
        )
    endif()
 endif()
endfunction()

###############################################################################
###############################################################################
# ADD LIBRARY
###############################################################################
###############################################################################
macro(CUDA_ADD_LIBRARY cuda_target)

  CUDA_ADD_CUDA_INCLUDE_ONCE()

  # Separate the sources from the options
  CUDA_GET_SOURCES_AND_OPTIONS(_sources _cmake_options _options ${ARGN})
  CUDA_BUILD_SHARED_LIBRARY(_cuda_shared_flag ${ARGN})
  # Create custom commands and targets for each file.
  CUDA_WRAP_SRCS( ${cuda_target} OBJ _generated_files ${_sources}
    ${_cmake_options} ${_cuda_shared_flag}
    OPTIONS ${_options} )

  # Compute the file name of the intermediate link file used for separable
  # compilation.
  CUDA_COMPUTE_SEPARABLE_COMPILATION_OBJECT_FILE_NAME(link_file ${cuda_target} "${${cuda_target}_SEPARABLE_COMPILATION_OBJECTS}")

  # Add the library.
  add_library(${cuda_target} ${_cmake_options}
    ${_generated_files}
    ${_sources}
    ${link_file}
    )

  # Add a link phase for the separable compilation if it has been enabled.  If
  # it has been enabled then the ${cuda_target}_SEPARABLE_COMPILATION_OBJECTS
  # variable will have been defined.
  CUDA_LINK_SEPARABLE_COMPILATION_OBJECTS("${link_file}" ${cuda_target} "${_options}" "${${cuda_target}_SEPARABLE_COMPILATION_OBJECTS}")

  target_link_libraries(${cuda_target} LINK_PRIVATE
    ${CUDA_LIBRARIES}
    )

  if(CUDA_SEPARABLE_COMPILATION)
    target_link_libraries(${cuda_target} ${CUDA_LINK_LIBRARIES_KEYWORD}
      ${CUDA_cudadevrt_LIBRARY}
      )
  endif()

  # We need to set the linker language based on what the expected generated file
  # would be. CUDA_C_OR_CXX is computed based on CUDA_HOST_COMPILATION_CPP.
  set_target_properties(${cuda_target}
    PROPERTIES
    LINKER_LANGUAGE CXX
    )

endmacro()


###############################################################################
###############################################################################
# ADD EXECUTABLE
###############################################################################
###############################################################################
macro(CUDA_ADD_EXECUTABLE cuda_target)

  CUDA_ADD_CUDA_INCLUDE_ONCE()

  # Separate the sources from the options
  CUDA_GET_SOURCES_AND_OPTIONS(_sources _cmake_options _options ${ARGN})
  # Create custom commands and targets for each file.
  CUDA_WRAP_SRCS( ${cuda_target} OBJ _generated_files ${_sources} OPTIONS ${_options} )

  # Compute the file name of the intermediate link file used for separable
  # compilation.
  CUDA_COMPUTE_SEPARABLE_COMPILATION_OBJECT_FILE_NAME(link_file ${cuda_target} "${${cuda_target}_SEPARABLE_COMPILATION_OBJECTS}")

  # Add the library.
  add_executable(${cuda_target} ${_cmake_options}
    ${_generated_files}
    ${_sources}
    ${link_file}
    )

  # Add a link phase for the separable compilation if it has been enabled.  If
  # it has been enabled then the ${cuda_target}_SEPARABLE_COMPILATION_OBJECTS
  # variable will have been defined.
  CUDA_LINK_SEPARABLE_COMPILATION_OBJECTS("${link_file}" ${cuda_target} "${_options}" "${${cuda_target}_SEPARABLE_COMPILATION_OBJECTS}")

  target_link_libraries(${cuda_target} ${CUDA_LINK_LIBRARIES_KEYWORD}
    ${CUDA_LIBRARIES}
    )

  set_target_properties(${cuda_target} PROPERTIES LINKER_LANGUAGE CXX)

endmacro()


###############################################################################
###############################################################################
# (Internal) helper for manually added cuda source files with specific targets
###############################################################################
###############################################################################
macro(cuda_compile_base cuda_target format generated_files)
  # Update a counter in this directory, to keep phony target names unique.
  set(_cuda_target "${cuda_target}")
  get_property(_counter DIRECTORY PROPERTY _cuda_internal_phony_counter)
  if(_counter)
    math(EXPR _counter "${_counter} + 1")
  else()
    set(_counter 1)
  endif()
  string(APPEND _cuda_target "_${_counter}")
  set_property(DIRECTORY PROPERTY _cuda_internal_phony_counter ${_counter})

  # Separate the sources from the options
  CUDA_GET_SOURCES_AND_OPTIONS(_sources _cmake_options _options ${ARGN})

  # Create custom commands and targets for each file.
  CUDA_WRAP_SRCS( ${_cuda_target} ${format} _generated_files ${_sources}
                  ${_cmake_options} OPTIONS ${_options} PHONY)

  set( ${generated_files} ${_generated_files})

endmacro()

macro(CUDA_COMPILE generated_files)
  cuda_compile_base(cuda_compile OBJ ${generated_files} ${ARGN})
endmacro()

macro(CUDA_COMPILE_PTX generated_files)
  cuda_compile_base(cuda_compile_ptx PTX ${generated_files} ${ARGN})
endmacro()

macro(CUDA_COMPILE_FATBIN generated_files)
  cuda_compile_base(cuda_compile_fatbin FATBIN ${generated_files} ${ARGN})
endmacro()

macro(CUDA_COMPILE_CUBIN generated_files)
  cuda_compile_base(cuda_compile_cubin CUBIN ${generated_files} ${ARGN})
endmacro()

macro(CUDA_ADD_CUFFT_TO_TARGET target)
  target_link_libraries(${target} ${CUDA_LINK_LIBRARIES_KEYWORD} ${CUDA_cufft_LIBRARY})
endmacro()

macro(CUDA_ADD_CUBLAS_TO_TARGET target)
  target_link_libraries(${target} ${CUDA_LINK_LIBRARIES_KEYWORD} ${CUDA_cublas_LIBRARY} ${CUDA_cublas_device_LIBRARY})
endmacro()

macro(CUDA_BUILD_CLEAN_TARGET)
  # Call this after you add all your CUDA targets, and you will get a
  # convenience target.  You should also make clean after running this target
  # to get the build system to generate all the code again.

  set(cuda_clean_target_name clean_cuda_depends)
  if (CMAKE_GENERATOR MATCHES "Visual Studio")
    string(TOUPPER ${cuda_clean_target_name} cuda_clean_target_name)
  endif()
  add_custom_target(${cuda_clean_target_name}
    COMMAND ${CMAKE_COMMAND} -E rm -f ${CUDA_ADDITIONAL_CLEAN_FILES})

  # Clear out the variable, so the next time we configure it will be empty.
  # This is useful so that the files won't persist in the list after targets
  # have been removed.
  set(CUDA_ADDITIONAL_CLEAN_FILES "" CACHE INTERNAL "List of intermediate files that are part of the cuda dependency scanning.")
endmacro()
