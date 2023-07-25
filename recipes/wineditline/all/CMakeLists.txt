cmake_minimum_required(VERSION 3.1)
project(WinEditLine C)

add_library(edit
    src/editline.c
    src/fn_complete.c
    src/history.c
    src/libedit.def
)
target_include_directories(edit PRIVATE src)

include(GNUInstallDirs)
install(TARGETS edit)
install(DIRECTORY src/editline DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")
