cmake_minimum_required(VERSION 3.15)
project(geotrans LANGUAGES CXX)

####
# Sources
####
file(GLOB_RECURSE DTCCSRCS "CCS/src/dtcc/CoordinateSystems/*.cpp")
set(CCSSRCS
    CCS/src/CoordinateConversion/CoordinateConversionService.cpp
)
file(GLOB_RECURSE CCSERVICESRCS "CCS/src/dtcc/*.cpp")
list(FILTER CCSERVICESRCS EXCLUDE REGEX ".*CCS/src/dtcc/CoordinateSystems.*")
set(SRCS
    GEOTRANS3/java_gui/geotrans3/jni/strtoval.cpp
    GEOTRANS3/java_gui/geotrans3/jni/fiomeths.cpp
)

####
# Includes
####

# Construct DTCC includes
file(GLOB_RECURSE DTCC_HEADERS "CCS/src/dtcc/CoordinateSystems/*.h")
set(DTTCINCS)
foreach(file ${DTCC_HEADERS})
    get_filename_component(DIR_PATH ${file} PATH)
    list(APPEND DTTCINCS ${DIR_PATH})
endforeach()
list(REMOVE_DUPLICATES DTTCINCS)

# Construct CCS includes. This is all headers not in DTTCINCS
file(GLOB_RECURSE CCS_HEADERS "CCS/src/*.h")
set(INCS GEOTRANS3/java_gui/geotrans3/jni)
foreach(file ${CCS_HEADERS})
    get_filename_component(DIR_PATH ${file} PATH)
    list(APPEND INCS ${DIR_PATH})
endforeach()
list(REMOVE_DUPLICATES INCS)
list(FILTER INCS EXCLUDE REGEX ".*CCS/src/dtcc/CoordinateSystems.*")

set(PUBLIC_HEADERS ${DTCC_HEADERS} ${CCS_HEADERS})

####
# Dependencies
####

find_package(Threads REQUIRED)
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
# Create libMSPdtcc
add_library(MSPdtcc ${DTCCSRCS} ${CCSERVICESRCS})
target_compile_features(MSPdtcc PUBLIC cxx_std_11)
if (WIN32)
    add_compile_definitions(MSPdtcc PRIVATE LITTLE_ENDIAN=1)
endif()
target_include_directories(MSPdtcc PUBLIC include ${DTTCINCS} ${INCS})
target_link_libraries(MSPdtcc PRIVATE Threads::Threads)

# Create libMSPCoordinateConversionService
add_library(MSPCoordinateConversionService ${CCSSRCS} ${CCSERVICESRCS})
target_compile_features(MSPCoordinateConversionService PUBLIC cxx_std_11)
target_include_directories(MSPCoordinateConversionService PUBLIC include ${DTTCINCS} ${INCS})
target_link_libraries(MSPCoordinateConversionService PUBLIC MSPdtcc)

include(GNUInstallDirs)
install(TARGETS MSPdtcc MSPCoordinateConversionService
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
install(FILES ${PUBLIC_HEADERS} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/geotrans)
install(DIRECTORY "data/" DESTINATION ${CMAKE_INSTALL_DATADIR})
