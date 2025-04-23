cmake_minimum_required(VERSION 3.15)
project(klib LANGUAGES C)

file(GLOB sources "*.c")
add_library(klib ${sources})
target_include_directories(klib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

include(GNUInstallDirs)
install(TARGETS klib
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
file(GLOB headers "*.h")
install(FILES ${headers} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/klib)
