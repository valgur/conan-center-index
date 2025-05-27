cmake_minimum_required(VERSION 3.15)
project(ufbx C)

add_library(ufbx ufbx.c)

set_target_properties(ufbx PROPERTIES
    PUBLIC_HEADER ufbx.h
    OUTPUT_NAME ufbx
    # As a C library, this is not too worriesome
    WINDOWS_EXPORT_ALL_SYMBOLS ON
)

include(GNUInstallDirs)
install(TARGETS ufbx)
