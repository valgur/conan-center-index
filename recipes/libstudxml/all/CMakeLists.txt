cmake_minimum_required(VERSION 3.15)
project(libstudxml LANGUAGES C CXX)

find_package(expat REQUIRED CONFIG)

add_library(studxml
    libstudxml/parser.cxx
    libstudxml/qname.cxx
    libstudxml/serializer.cxx
    libstudxml/value-traits.cxx
    libstudxml/details/genx/char-props.c
    libstudxml/details/genx/genx.c
)
target_include_directories(studxml PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(studxml PUBLIC expat::expat)

if(BUILD_SHARED_LIBS)
    target_compile_definitions(studxml
        PRIVATE LIBSTUDXML_SHARED_BUILD
        INTERFACE LIBSTUDXML_SHARED
    )
else()
    target_compile_definitions(studxml
        PRIVATE LIBSTUDXML_STATIC_BUILD
        INTERFACE LIBSTUDXML_STATIC
    )
endif()

include(GNUInstallDirs)
install(
    TARGETS studxml
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
install(
    DIRECTORY libstudxml
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
    FILES_MATCHING REGEX "(.*).(h|hxx|ixx|txx)$"
)
