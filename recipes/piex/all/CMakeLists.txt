# Reproduces https://github.com/google/piex/blob/v0.27/piex.gyp
cmake_minimum_required(VERSION 3.15)
project(piex LANGUAGES CXX)

include_directories(.)

add_library(binary_parse
    src/binary_parse/cached_paged_byte_array.cc
    src/binary_parse/range_checked_byte_ptr.cc
)

add_library(image_type_recognition
    src/image_type_recognition/image_type_recognition_lite.cc
)
target_link_libraries(image_type_recognition PRIVATE binary_parse)

add_library(tiff_directory
    src/tiff_directory/tiff_directory.cc
)
target_link_libraries(tiff_directory PRIVATE binary_parse)

add_library(piex
    src/piex.cc
    src/piex_cr3.cc
    src/tiff_parser.cc
)
target_link_libraries(piex PRIVATE binary_parse image_type_recognition tiff_directory)

install(
    TARGETS
        piex
        binary_parse
        image_type_recognition
        tiff_directory
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(
    DIRECTORY src/
    DESTINATION include/src
    FILES_MATCHING PATTERN "*.h"
)
