cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(X11 REQUIRED)

if(NOT _USING_CONAN_FindX11)
    message(FATAL_ERROR "Failed to load conan-findx11.cmake")
endif()

add_executable(test_package test_package.c)
target_link_libraries(test_package PRIVATE
    X11::ICE
    X11::SM
    X11::X11
    X11::Xau
    X11::xcb
    X11::X11_xcb
    X11::xcb_composite
    X11::xcb_cursor
    X11::xcb_damage
    X11::xcb_dpms
    X11::xcb_dri2
    X11::xcb_dri3
    X11::xcb_errors
    X11::xcb_ewmh
    X11::xcb_glx
    X11::xcb_icccm
    X11::xcb_image
    X11::xcb_keysyms
    X11::xcb_present
    X11::xcb_randr
    X11::xcb_record
    X11::xcb_render
    X11::xcb_render_util
    X11::xcb_res
    X11::xcb_screensaver
    X11::xcb_shape
    X11::xcb_shm
    X11::xcb_sync
    X11::xcb_util
    X11::xcb_xf86dri
    X11::xcb_xfixes
    X11::xcb_xinerama
    X11::xcb_xinput
    X11::xcb_xkb
    X11::xcb_xrm
    X11::xcb_xtest
    X11::xcb_xvmc
    X11::xcb_xv
    X11::Xcomposite
    X11::Xcursor
    X11::Xdamage
    X11::Xdmcp
    X11::Xext
    X11::Xxf86vm
    X11::Xfixes
    X11::Xi
    X11::Xinerama
    X11::Xkb
    X11::xkbfile
    X11::Xmu
    X11::Xpm
    X11::Xtst
    X11::Xrandr
    X11::Xrender
    X11::XRes
    X11::Xss
    X11::Xt
    X11::Xutil
    X11::Xv
    X11::Xaw
)
if(FULL_TEST)
    target_link_libraries(test_package PRIVATE
        X11::Xft
        X11::xkbcommon
        X11::xkbcommon_X11
    )
endif()
