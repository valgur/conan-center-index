# Reproduces https://cmake.org/cmake/help/v3.30/module/FindX11.html
# https://github.com/Kitware/CMake/blob/v3.30.4/Modules/FindX11.cmake

if(DEFINED _USING_CONAN_FindX11)
    return()
endif()
set(_USING_CONAN_FindX11 1)

# These are set by CMakeDeps automatically
# X11_FOUND        - True if X11 is available
# X11_INCLUDE_DIR  - include directories to use X11
# X11_LIBRARIES    - link against these to use X11

# X11_X11_INCLUDE_PATH,            X11_X11_LIB,                                      X11::X11
set(X11_X11_FOUND TRUE)
set(X11_X11_INCLUDE_PATH "${X11_INCLUDE_DIR}")
set(X11_X11_LIB X11::X11)

# X11_X11_xcb_INCLUDE_PATH,        X11_X11_xcb_LIB,        X11_X11_xcb_FOUND,        X11::X11_xcb
set(X11_X11_xcb_FOUND TRUE)
set(X11_X11_xcb_INCLUDE_PATH "${X11_INCLUDE_DIR}")
set(X11_X11_xcb_LIB X11::X11_xcb)

# X11_Xkblib_INCLUDE_PATH,                                 X11_Xkb_FOUND,            X11::Xkb
set(X11_Xkb_FOUND TRUE)
set(X11_Xkblib_INCLUDE_PATH "${X11_INCLUDE_DIR}")
set(X11_Xkb_LIB X11::Xkb)
if(NOT TARGET X11::Xkb)
    add_library(X11::Xkb INTERFACE IMPORTED)
    target_include_directories(X11::Xkb INTERFACE "${X11_INCLUDE_DIR}")
endif()

# X11_Xutil_INCLUDE_PATH,                                  X11_Xutil_FOUND,          X11::Xutil
set(X11_Xutil_FOUND TRUE)
set(X11_Xutil_INCLUDE_PATH "${X11_INCLUDE_DIR}")
set(X11_Xutil_LIB X11::Xutil)
if(NOT TARGET X11::Xutil)
    add_library(X11::Xutil INTERFACE IMPORTED)
    target_include_directories(X11::Xutil INTERFACE "${X11_INCLUDE_DIR}")
endif()

# X11_ICE_INCLUDE_PATH,            X11_ICE_LIB,            X11_ICE_FOUND,            X11::ICE
find_package(libice CONFIG QUIET)
set(X11_ICE_FOUND ${libice_FOUND})
if(X11_ICE_FOUND)
    set(X11_ICE_INCLUDE_PATH "${libice_INCLUDE_DIR}")
    set(X11_ICE_LIB X11::ICE)
    list(APPEND X11_INCLUDE_DIR "${X11_ICE_INCLUDE_PATH}")
    list(APPEND X11_LIBRARIES X11::ICE)
endif()

# X11_SM_INCLUDE_PATH,             X11_SM_LIB,             X11_SM_FOUND,             X11::SM
find_package(libsm CONFIG QUIET)
set(X11_SM_FOUND ${libsm_FOUND})
if(X11_SM_FOUND)
    set(X11_SM_INCLUDE_PATH "${libsm_INCLUDE_DIR}")
    set(X11_SM_LIB X11::SM)
    list(APPEND X11_INCLUDE_DIR "${X11_SM_INCLUDE_PATH}")
    list(APPEND X11_LIBRARIES X11::SM)
endif()

# X11_Xaccessstr_INCLUDE_PATH,                             X11_Xaccess_FOUND
# X11_Xkb_INCLUDE_PATH,
find_package(xorg-proto CONFIG QUIET)
set(X11_Xaccess_FOUND ${xorg-proto_FOUND})
if(xorg-proto_FOUND)
    set(X11_Xaccess_INCLUDE_PATH "${xorg-proto_INCLUDE_DIRS}")
    set(X11_Xkb_INCLUDE_PATH "${xorg-proto_INCLUDE_DIRS}")
    list(APPEND X11_INCLUDE_DIR ${X11_Xaccess_INCLUDE_PATH})
endif()

# X11_Xau_INCLUDE_PATH,            X11_Xau_LIB,            X11_Xau_FOUND,            X11::Xau
find_package(libxau CONFIG QUIET)
set(X11_Xau_FOUND ${libxau_FOUND})
if(X11_Xau_FOUND)
    set(X11_Xau_INCLUDE_PATH "${libxau_INCLUDE_DIR}")
    set(X11_Xau_LIB X11::Xau)
endif()

find_package(libxcb CONFIG QUIET)
set(X11_xcb_FOUND ${libxcb_FOUND})
set(X11_xcb_composite_FOUND ${libxcb_FOUND})
set(X11_xcb_damage_FOUND ${libxcb_FOUND})
set(X11_xcb_dbe_FOUND ${libxcb_FOUND})
set(X11_xcb_dpms_FOUND ${libxcb_FOUND})
set(X11_xcb_dri2_FOUND ${libxcb_FOUND})
set(X11_xcb_dri3_FOUND ${libxcb_FOUND})
set(X11_xcb_ge_FOUND ${libxcb_FOUND})
set(X11_xcb_glx_FOUND ${libxcb_FOUND})
set(X11_xcb_present_FOUND ${libxcb_FOUND})
set(X11_xcb_randr_FOUND ${libxcb_FOUND})
set(X11_xcb_record_FOUND ${libxcb_FOUND})
set(X11_xcb_render_FOUND ${libxcb_FOUND})
set(X11_xcb_res_FOUND ${libxcb_FOUND})
set(X11_xcb_screensaver_FOUND ${libxcb_FOUND})
set(X11_xcb_shape_FOUND ${libxcb_FOUND})
set(X11_xcb_shm_FOUND ${libxcb_FOUND})
set(X11_xcb_sync_FOUND ${libxcb_FOUND})
set(X11_xcb_xevie_FOUND ${libxcb_FOUND})
set(X11_xcb_xf86dri_FOUND ${libxcb_FOUND})
set(X11_xcb_xfixes_FOUND ${libxcb_FOUND})
set(X11_xcb_xinerama_FOUND ${libxcb_FOUND})
set(X11_xcb_xinput_FOUND ${libxcb_FOUND})
set(X11_xcb_xkb_FOUND ${libxcb_FOUND})
set(X11_xcb_xprint_FOUND ${libxcb_FOUND})
set(X11_xcb_xselinux_FOUND ${libxcb_FOUND})
set(X11_xcb_xtest_FOUND ${libxcb_FOUND})
set(X11_xcb_xv_FOUND ${libxcb_FOUND})
set(X11_xcb_xvmc_FOUND ${libxcb_FOUND})
if(libxcb_FOUND)
    # X11_xcb_INCLUDE_PATH,            X11_xcb_LIB,            X11_xcb_FOUND,            X11::xcb
    set(X11_xcb_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_LIB X11::xcb)

    # X11_xcb_composite_INCLUDE_PATH,  X11_xcb_composite_LIB,  X11_xcb_composite_FOUND,  X11::xcb_composite
    set(X11_xcb_composite_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_composite_LIB X11::xcb_composite)

    # X11_xcb_damage_INCLUDE_PATH,     X11_xcb_damage_LIB,     X11_xcb_damage_FOUND,     X11::xcb_damage
    set(X11_xcb_damage_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_damage_LIB X11::xcb_damage)

    # X11::xcb_dbe (unofficial)
    set(X11_xcb_dbe_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_dbe_LIB X11::xcb_dbe)

    # X11_xcb_dpms_INCLUDE_PATH,       X11_xcb_dpms_LIB,       X11_xcb_dpms_FOUND,       X11::xcb_dpms
    set(X11_xcb_dpms_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_dpms_LIB X11::xcb_dpms)

    # X11_xcb_dri2_INCLUDE_PATH,       X11_xcb_dri2_LIB,       X11_xcb_dri2_FOUND,       X11::xcb_dri2
    set(X11_xcb_dri2_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_dri2_LIB X11::xcb_dri2)

    # X11_xcb_dri3_INCLUDE_PATH,       X11_xcb_dri3_LIB,       X11_xcb_dri3_FOUND,       X11::xcb_dri3
    if(TARGET X11::xcb_dri3)
        set(X11_xcb_dri3_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
        set(X11_xcb_dri3_LIB X11::xcb_dri3)
    else()
        set(X11_xcb_dri3_FOUND FALSE)
    endif()

    # X11::xcb_ge (unofficial)
    if(TARGET X11::xcb_ge)
        set(X11_xcb_ge_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
        set(X11_xcb_ge_LIB X11::xcb_ge)
    else()
        set(X11_xcb_ge_FOUND FALSE)
    endif()

    # X11_xcb_glx_INCLUDE_PATH,        X11_xcb_glx_LIB,        X11_xcb_glx_FOUND,        X11::xcb_glx
    set(X11_xcb_glx_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_glx_LIB X11::xcb_glx)

    # X11_xcb_present_INCLUDE_PATH,    X11_xcb_present_LIB,    X11_xcb_present_FOUND,    X11::xcb_present
    set(X11_xcb_present_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_present_LIB X11::xcb_present)

    # X11_xcb_randr_INCLUDE_PATH,      X11_xcb_randr_LIB,      X11_xcb_randr_FOUND,      X11::xcb_randr
    set(X11_xcb_randr_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_randr_LIB X11::xcb_randr)

    # X11_xcb_record_INCLUDE_PATH,     X11_xcb_record_LIB,     X11_xcb_record_FOUND,     X11::xcb_record
    set(X11_xcb_record_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_record_LIB X11::xcb_record)

    # X11_xcb_render_INCLUDE_PATH,     X11_xcb_render_LIB,     X11_xcb_render_FOUND,     X11::xcb_render
    set(X11_xcb_render_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_render_LIB X11::xcb_render)

    # X11_xcb_res_INCLUDE_PATH,        X11_xcb_res_LIB,        X11_xcb_res_FOUND,        X11::xcb_res
    set(X11_xcb_res_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_res_LIB X11::xcb_res)

    # X11_xcb_screensaver_INCLUDE_PATH,X11_xcb_screensaver_LIB,X11_xcb_screensaver_FOUND,X11::xcb_screensaver
    set(X11_xcb_screensaver_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_screensaver_LIB X11::xcb_screensaver)

    # X11_xcb_shape_INCLUDE_PATH,      X11_xcb_shape_LIB,      X11_xcb_shape_FOUND,      X11::xcb_shape
    set(X11_xcb_shape_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_shape_LIB X11::xcb_shape)

    # X11_xcb_shm_INCLUDE_PATH,        X11_xcb_shm_LIB,        X11_xcb_shm_FOUND,        X11::xcb_shm
    set(X11_xcb_shm_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_shm_LIB X11::xcb_shm)

    # X11_xcb_sync_INCLUDE_PATH,       X11_xcb_sync_LIB,       X11_xcb_sync_FOUND,       X11::xcb_sync
    set(X11_xcb_sync_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_sync_LIB X11::xcb_sync)

    # X11::xcb_xevie (unofficial)
    if(TARGET X11::xcb_xevie)
        set(X11_xcb_xevie_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
        set(X11_xcb_xevie_LIB X11::xcb_xevie)
    else()
        set(X11_xcb_xevie_FOUND FALSE)
    endif()

    # X11_xcb_xf86dri_INCLUDE_PATH,    X11_xcb_xf86dri_LIB,    X11_xcb_xf86dri_FOUND,    X11::xcb_xf86dri
    set(X11_xcb_xf86dri_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xf86dri_LIB X11::xcb_xf86dri)

    # X11_xcb_xfixes_INCLUDE_PATH,     X11_xcb_xfixes_LIB,     X11_xcb_xfixes_FOUND,     X11::xcb_xfixes
    set(X11_xcb_xfixes_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xfixes_LIB X11::xcb_xfixes)

    # X11_xcb_xinerama_INCLUDE_PATH,   X11_xcb_xinerama_LIB,   X11_xcb_xinerama_FOUND,   X11::xcb_xinerama
    set(X11_xcb_xinerama_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xinerama_LIB X11::xcb_xinerama)

    # X11_xcb_xinput_INCLUDE_PATH,     X11_xcb_xinput_LIB,     X11_xcb_xinput_FOUND,     X11::xcb_xinput
    set(X11_xcb_xinput_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xinput_LIB X11::xcb_xinput)

    # X11_xcb_xkb_INCLUDE_PATH,        X11_xcb_xkb_LIB,        X11_xcb_xkb_FOUND,        X11::xcb_xkb
    set(X11_xcb_xkb_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xkb_LIB X11::xcb_xkb)

    # X11::xcb_xprint (unofficial)
    if(TARGET X11::xcb_xprint)
        set(X11_xcb_xprint_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
        set(X11_xcb_xprint_LIB X11::xcb_xprint)
    else()
        set(X11_xcb_xprint_FOUND FALSE)
    endif()

    # X11::xcb_xselinux (unofficial)
    if(TARGET X11::xcb_xselinux)
        set(X11_xcb_xselinux_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
        set(X11_xcb_xselinux_LIB X11::xcb_xselinux)
    else()
        set(X11_xcb_xselinux_FOUND FALSE)
    endif()

    # X11_xcb_xtest_INCLUDE_PATH,      X11_xcb_xtest_LIB,      X11_xcb_xtest_FOUND,      X11::xcb_xtest
    set(X11_xcb_xtest_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xtest_LIB X11::xcb_xtest)

    # X11_xcb_xv_INCLUDE_PATH,         X11_xcb_xv_LIB,         X11_xcb_xv_FOUND          X11::xcb_xv
    set(X11_xcb_xv_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xv_LIB X11::xcb_xv)

    # X11_xcb_xvmc_INCLUDE_PATH,       X11_xcb_xvmc_LIB,       X11_xcb_xvmc_FOUND,       X11::xcb_xvmc
    set(X11_xcb_xvmc_INCLUDE_PATH "${libxcb_INCLUDE_DIR}")
    set(X11_xcb_xvmc_LIB X11::xcb_xvmc)
endif()

# X11_xcb_util_INCLUDE_PATH,       X11_xcb_util_LIB,       X11_xcb_util_FOUND,       X11::xcb_util
find_package(xcb-util CONFIG QUIET)
set(X11_xcb_util_FOUND ${xcb-util_FOUND})
if(xcb-util_FOUND)
    set(X11_xcb_util_INCLUDE_PATH "${xcb-util_INCLUDE_DIRS}")
    set(X11_xcb_util_LIB X11::xcb_util)
endif()

# X11_xcb_cursor_INCLUDE_PATH,     X11_xcb_cursor_LIB,     X11_xcb_cursor_FOUND,     X11::xcb_cursor
find_package(xcb-util-cursor CONFIG QUIET)
set(X11_xcb_cursor_FOUND ${xcb-util-cursor_FOUND})
if(xcb-util-cursor_FOUND)
    set(X11_xcb_cursor_INCLUDE_PATH "${xcb-util-cursor_INCLUDE_DIRS}")
    set(X11_xcb_cursor_LIB X11::xcb_cursor)
endif()

# X11_xcb_errors_INCLUDE_PATH,     X11_xcb_errors_LIB,     X11_xcb_errors_FOUND,     X11::xcb_errors
find_package(xcb-util-errors CONFIG QUIET)
set(X11_xcb_errors_FOUND ${xcb-util-errors_FOUND})
if(xcb-util-errors_FOUND)
    set(X11_xcb_errors_INCLUDE_PATH "${xcb-util-errors_INCLUDE_DIRS}")
    set(X11_xcb_errors_LIB X11::xcb_errors)
endif()

# X11_xcb_image_INCLUDE_PATH,      X11_xcb_image_LIB,      X11_xcb_image_FOUND,      X11::xcb_image
find_package(xcb-util-image CONFIG QUIET)
set(X11_xcb_image_FOUND ${xcb-util-image_FOUND})
if(xcb-util-image_FOUND)
    set(X11_xcb_image_INCLUDE_PATH "${xcb-util-image_INCLUDE_DIRS}")
    set(X11_xcb_image_LIB X11::xcb_image)
endif()

# X11_xcb_keysyms_INCLUDE_PATH,    X11_xcb_keysyms_LIB,    X11_xcb_keysyms_FOUND,    X11::xcb_keysyms
find_package(xcb-util-keysyms CONFIG QUIET)
set(X11_xcb_keysyms_FOUND ${xcb-util-keysyms_FOUND})
if(xcb-util-keysyms_FOUND)
    set(X11_xcb_keysyms_INCLUDE_PATH "${xcb-util-keysyms_INCLUDE_DIRS}")
    set(X11_xcb_keysyms_LIB X11::xcb_keysyms)
endif()

# X11_xcb_render_util_INCLUDE_PATH,X11_xcb_render_util_LIB,X11_xcb_render_util_FOUND,X11::xcb_render_util
find_package(xcb-util-renderutil CONFIG QUIET)
set(X11_xcb_render_util_FOUND ${xcb-util-renderutil_FOUND})
if(xcb-util-renderutil_FOUND)
    set(X11_xcb_render_util_INCLUDE_PATH "${xcb-util-renderutil_INCLUDE_DIRS}")
    set(X11_xcb_render_util_LIB X11::xcb_render_util)
endif()

# X11_xcb_ewmh_INCLUDE_PATH,       X11_xcb_ewmh_LIB,       X11_xcb_ewmh_FOUND,       X11::xcb_ewmh
# X11_xcb_icccm_INCLUDE_PATH,      X11_xcb_icccm_LIB,      X11_xcb_icccm_FOUND,      X11::xcb_icccm
find_package(xcb-util-wm CONFIG QUIET)
set(X11_xcb_ewmh_FOUND ${xcb-util-wm_FOUND})
set(X11_xcb_icccm_FOUND ${xcb-util-wm_FOUND})
if(xcb-util-wm_FOUND)
    set(X11_xcb_ewmh_INCLUDE_PATH "${xcb-util-wm_INCLUDE_DIRS}")
    set(X11_xcb_ewmh_LIB X11::xcb_ewmh)
    set(X11_xcb_icccm_INCLUDE_PATH "${xcb-util-wm_INCLUDE_DIRS}")
    set(X11_xcb_icccm_LIB X11::xcb_icccm)
endif()

# X11_xcb_xrm_INCLUDE_PATH,        X11_xcb_xrm_LIB,        X11_xcb_xrm_FOUND,        X11::xcb_xrm
find_package(xcb-util-xrm CONFIG QUIET)
set(X11_xcb_xrm_FOUND ${xcb-util-xrm_FOUND})
if(xcb-util-xrm_FOUND)
    set(X11_xcb_xrm_INCLUDE_PATH "${xcb-util-xrm_INCLUDE_DIRS}")
    set(X11_xcb_xrm_LIB X11::xcb_xrm)
endif()

# X11_Xcomposite_INCLUDE_PATH,     X11_Xcomposite_LIB,     X11_Xcomposite_FOUND,     X11::Xcomposite
find_package(libxcomposite CONFIG QUIET)
set(X11_Xcomposite_FOUND ${libxcomposite_FOUND})
if(libxcomposite_FOUND)
    set(X11_Xcomposite_INCLUDE_PATH "${libxcomposite_INCLUDE_DIR}")
    set(X11_Xcomposite_LIB X11::Xcomposite)
    list(APPEND X11_INCLUDE_DIR ${X11_Xcomposite_INCLUDE_PATH})
endif()

# X11_Xcursor_INCLUDE_PATH,        X11_Xcursor_LIB,        X11_Xcursor_FOUND,        X11::Xcursor
find_package(libxcursor CONFIG QUIET)
set(X11_Xcursor_FOUND ${libxcursor_FOUND})
if(libxcursor_FOUND)
    set(X11_Xcursor_INCLUDE_PATH "${libxcursor_INCLUDE_DIR}")
    set(X11_Xcursor_LIB X11::Xcursor)
    list(APPEND X11_INCLUDE_DIR ${X11_Xcursor_INCLUDE_PATH})
endif()

# X11_Xdamage_INCLUDE_PATH,        X11_Xdamage_LIB,        X11_Xdamage_FOUND,        X11::Xdamage
find_package(libxdamage CONFIG QUIET)
set(X11_Xdamage_FOUND ${libxdamage_FOUND})
if(libxdamage_FOUND)
    set(X11_Xdamage_INCLUDE_PATH "${libxdamage_INCLUDE_DIR}")
    set(X11_Xdamage_LIB X11::Xdamage)
    list(APPEND X11_INCLUDE_DIR ${X11_Xdamage_INCLUDE_PATH})
endif()

# X11_Xdmcp_INCLUDE_PATH,          X11_Xdmcp_LIB,          X11_Xdmcp_FOUND,          X11::Xdmcp
find_package(libxdmcp CONFIG QUIET)
set(X11_Xdmcp_FOUND ${libxdmcp_FOUND})
if(libxdmcp_FOUND)
    set(X11_Xdmcp_INCLUDE_PATH "${libxdmcp_INCLUDE_DIR}")
    set(X11_Xdmcp_LIB X11::Xdmcp)
    list(APPEND X11_INCLUDE_DIR ${X11_Xdmcp_INCLUDE_PATH})
endif()

# X11_Xext_INCLUDE_PATH,           X11_Xext_LIB,           X11_Xext_FOUND,           X11::Xext
# X11_dpms_INCLUDE_PATH,           (in X11_Xext_LIB),      X11_dpms_FOUND
# X11_Xdbe_INCLUDE_PATH,           (in X11_Xext_LIB),      X11_Xdbe_FOUND
# X11_XShm_INCLUDE_PATH,           (in X11_Xext_LIB),      X11_XShm_FOUND
# X11_Xshape_INCLUDE_PATH,         (in X11_Xext_LIB),      X11_Xshape_FOUND
# X11_XSync_INCLUDE_PATH,          (in X11_Xext_LIB),      X11_XSync_FOUND
find_package(libxext CONFIG QUIET)
set(X11_Xext_FOUND ${libxext_FOUND})
set(X11_dpms_FOUND ${libxext_FOUND})
set(X11_Xdbe_FOUND ${libxext_FOUND})
set(X11_XShm_FOUND ${libxext_FOUND})
set(X11_Xshape_FOUND ${libxext_FOUND})
set(X11_XSync_FOUND ${libxext_FOUND})
if(libxext_FOUND)
    set(X11_Xext_INCLUDE_PATH "${libxext_INCLUDE_DIR}")
    set(X11_Xext_LIB X11::Xext)
    set(X11_dpms_INCLUDE_PATH "${libxext_INCLUDE_DIR}")
    set(X11_Xdbe_INCLUDE_PATH "${libxext_INCLUDE_DIR}")
    set(X11_XShm_INCLUDE_PATH "${libxext_INCLUDE_DIR}")
    set(X11_Xshape_INCLUDE_PATH "${libxext_INCLUDE_DIR}")
    set(X11_XSync_INCLUDE_PATH "${libxext_INCLUDE_DIR}")

    list(APPEND X11_LIBRARIES ${X11_Xext_LIB})
endif()

# X11_Xxf86vm_INCLUDE_PATH,        X11_Xxf86vm_LIB         X11_Xxf86vm_FOUND,        X11::Xxf86vm
find_package(libxxf86vm CONFIG QUIET)
set(X11_Xxf86vm_FOUND ${libxxf86vm_FOUND})
if(libxxf86vm_FOUND)
    set(X11_Xxf86vm_INCLUDE_PATH "${libxxf86vm_INCLUDE_DIR}")
    set(X11_Xxf86vm_LIB X11::Xxf86vm)
    list(APPEND X11_INCLUDE_DIR ${X11_Xxf86misc_INCLUDE_PATH})
endif()

# X11_Xfixes_INCLUDE_PATH,         X11_Xfixes_LIB,         X11_Xfixes_FOUND,         X11::Xfixes
find_package(libxfixes CONFIG QUIET)
set(X11_Xfixes_FOUND ${libxfixes_FOUND})
if(libxfixes_FOUND)
    set(X11_Xfixes_INCLUDE_PATH "${libxfixes_INCLUDE_DIR}")
    set(X11_Xfixes_LIB X11::Xfixes)
    list(APPEND X11_INCLUDE_DIR ${X11_Xfixes_INCLUDE_PATH})
endif()

# X11_Xft_INCLUDE_PATH,            X11_Xft_LIB,            X11_Xft_FOUND,            X11::Xft
find_package(libxft CONFIG QUIET)
set(X11_Xft_FOUND ${libxft_FOUND})
if(libxft_FOUND)
    set(X11_Xft_INCLUDE_PATH "${libxft_INCLUDE_DIR}")
    set(X11_Xft_LIB X11::Xft)
    list(APPEND X11_INCLUDE_DIR ${X11_Xft_INCLUDE_PATH})
endif()

# X11_Xi_INCLUDE_PATH,             X11_Xi_LIB,             X11_Xi_FOUND,             X11::Xi
find_package(libxi CONFIG QUIET)
set(X11_Xi_FOUND ${libxi_FOUND})
if(libxi_FOUND)
    set(X11_Xi_INCLUDE_PATH "${libxi_INCLUDE_DIR}")
    set(X11_Xi_LIB X11::Xi)
    list(APPEND X11_INCLUDE_DIR ${X11_Xi_INCLUDE_PATH})
endif()

# X11_Xinerama_INCLUDE_PATH,       X11_Xinerama_LIB,       X11_Xinerama_FOUND,       X11::Xinerama
find_package(libxinerama CONFIG QUIET)
set(X11_Xinerama_FOUND ${libxinerama_FOUND})
if(libxinerama_FOUND)
    set(X11_Xinerama_INCLUDE_PATH "${libxinerama_INCLUDE_DIR}")
    set(X11_Xinerama_LIB X11::Xinerama)
    list(APPEND X11_INCLUDE_DIR ${X11_Xinerama_INCLUDE_PATH})
endif()

# X11_xkbcommon_INCLUDE_PATH,      X11_xkbcommon_LIB,      X11_xkbcommon_FOUND,      X11::xkbcommon
# X11_xkbcommon_X11_INCLUDE_PATH,  X11_xkbcommon_X11_LIB,  X11_xkbcommon_X11_FOUND,  X11::xkbcommon_X11
find_package(xkbcommon CONFIG QUIET)
set(X11_xkbcommon_FOUND ${xkbcommon_FOUND})
set(X11_xkbcommon_X11_FOUND ${xkbcommon_FOUND})
if(xkbcommon_FOUND)
    set(X11_xkbcommon_INCLUDE_PATH "${xkbcommon_INCLUDE_DIRS}")
    set(X11_xkbcommon_LIB X11::xkbcommon)
    set(X11_xkbcommon_X11_INCLUDE_PATH "${xkbcommon_INCLUDE_DIRS}")
    set(X11_xkbcommon_X11_LIB X11::xkbcommon_X11)
endif()

# X11_xkbfile_INCLUDE_PATH,        X11_xkbfile_LIB,        X11_xkbfile_FOUND,        X11::xkbfile
# X11_Xaccessrules_INCLUDE_PATH,
find_package(libxkbfile CONFIG QUIET)
set(X11_xkbfile_FOUND ${libxkbfile_FOUND})
if(libxkbfile_FOUND)
    set(X11_xkbfile_INCLUDE_PATH "${libxkbfile_INCLUDE_DIR}")
    set(X11_xkbfile_LIB X11::xkbfile)
    set(X11_Xaccessrules_INCLUDE_PATH "${libxkbfile_INCLUDE_DIR}")
    list(APPEND X11_INCLUDE_DIR ${X11_xkbfile_INCLUDE_PATH})
endif()

# X11_Xmu_INCLUDE_PATH,            X11_Xmu_LIB,            X11_Xmu_FOUND,            X11::Xmu
find_package(libxmu CONFIG QUIET)
set(X11_Xmu_FOUND ${libxmu_FOUND})
if(libxmu_FOUND)
    set(X11_Xmu_INCLUDE_PATH "${libxmu_INCLUDE_DIR}")
    set(X11_Xmu_LIB X11::Xmu)
    list(APPEND X11_INCLUDE_DIR ${X11_Xmu_INCLUDE_PATH})
endif()

# X11_Xpm_INCLUDE_PATH,            X11_Xpm_LIB,            X11_Xpm_FOUND,            X11::Xpm
find_package(libxpm CONFIG QUIET)
set(X11_Xpm_FOUND ${libxpm_FOUND})
if(libxpm_FOUND)
    set(X11_Xpm_INCLUDE_PATH "${libxpm_INCLUDE_DIR}")
    set(X11_Xpm_LIB X11::Xpm)
    list(APPEND X11_INCLUDE_DIR ${X11_Xpm_INCLUDE_PATH})
endif()

# X11_Xtst_INCLUDE_PATH,           X11_Xtst_LIB,           X11_Xtst_FOUND,           X11::Xtst
find_package(libxtst CONFIG QUIET)
set(X11_Xtst_FOUND ${libxtst_FOUND})
if(libxtst_FOUND)
    set(X11_Xtst_INCLUDE_PATH "${libxtst_INCLUDE_DIR}")
    set(X11_Xtst_LIB X11::Xtst)
    list(APPEND X11_INCLUDE_DIR ${X11_Xtst_INCLUDE_PATH})
endif()

# X11_Xrandr_INCLUDE_PATH,         X11_Xrandr_LIB,         X11_Xrandr_FOUND,         X11::Xrandr
find_package(libxrandr CONFIG QUIET)
set(X11_Xrandr_FOUND ${libxrandr_FOUND})
if(libxrandr_FOUND)
    set(X11_Xrandr_INCLUDE_PATH "${libxrandr_INCLUDE_DIR}")
    set(X11_Xrandr_LIB X11::Xrandr)
    list(APPEND X11_INCLUDE_DIR ${X11_Xrandr_INCLUDE_PATH})
endif()

# X11_Xrender_INCLUDE_PATH,        X11_Xrender_LIB,        X11_Xrender_FOUND,        X11::Xrender
find_package(libxrender CONFIG QUIET)
set(X11_Xrender_FOUND ${libxrender_FOUND})
if(libxrender_FOUND)
    set(X11_Xrender_INCLUDE_PATH "${libxrender_INCLUDE_DIR}")
    set(X11_Xrender_LIB X11::Xrender)
    list(APPEND X11_INCLUDE_DIR ${X11_Xrender_INCLUDE_PATH})
endif()

# X11_XRes_INCLUDE_PATH,           X11_XRes_LIB,           X11_XRes_FOUND,           X11::XRes
find_package(libxres CONFIG QUIET)
set(X11_XRes_FOUND ${libxres_FOUND})
if(libxres_FOUND)
    set(X11_XRes_INCLUDE_PATH "${libxres_INCLUDE_DIR}")
    set(X11_XRes_LIB X11::XRes)
    list(APPEND X11_INCLUDE_DIR ${X11_XRes_INCLUDE_PATH})
endif()

# X11_Xss_INCLUDE_PATH,            X11_Xss_LIB,            X11_Xss_FOUND,            X11::Xss
find_package(libxss CONFIG QUIET)
set(X11_Xss_FOUND ${libxss_FOUND})
if(libxss_FOUND)
    set(X11_Xss_INCLUDE_PATH "${libxss_INCLUDE_DIR}")
    set(X11_Xss_LIB X11::Xss)
    list(APPEND X11_INCLUDE_DIR ${X11_Xss_INCLUDE_PATH})
endif()

# X11_Xt_INCLUDE_PATH,             X11_Xt_LIB,             X11_Xt_FOUND,             X11::Xt
find_package(libxt CONFIG QUIET)
set(X11_Xt_FOUND ${libxt_FOUND})
if(libxt_FOUND)
    set(X11_Xt_INCLUDE_PATH "${libxt_INCLUDE_DIR}")
    set(X11_Xt_LIB X11::Xt)
endif()

# X11_Xv_INCLUDE_PATH,             X11_Xv_LIB,             X11_Xv_FOUND,             X11::Xv
find_package(libxv CONFIG QUIET)
set(X11_Xv_FOUND ${libxv_FOUND})
if(libxv_FOUND)
    set(X11_Xv_INCLUDE_PATH "${libxv_INCLUDE_DIR}")
    set(X11_Xv_LIB X11::Xv)
    list(APPEND X11_INCLUDE_DIR ${X11_Xv_INCLUDE_PATH})
endif()

# X11_Xaw_INCLUDE_PATH,            X11_Xaw_LIB             X11_Xaw_FOUND             X11::Xaw
find_package(libxaw CONFIG QUIET)
set(X11_Xaw_FOUND ${libxaw_FOUND})
if(libxaw_FOUND)
    set(X11_Xaw_INCLUDE_PATH "${libxaw_INCLUDE_DIR}")
    set(X11_Xaw_LIB X11::Xaw)
endif()

# Not provided by modern library versions:
# X11_Xxf86misc_INCLUDE_PATH,      X11_Xxf86misc_LIB,      X11_Xxf86misc_FOUND,      X11::Xxf86misc

if (X11_Xaccessrules_INCLUDE_PATH AND X11_Xaccessstr_INCLUDE_PATH)
    set(X11_Xaccess_FOUND TRUE)
    set(X11_Xaccess_INCLUDE_PATH "${X11_Xaccessstr_INCLUDE_PATH}")
endif()

# Backwards compatibility.
set(X11_XTest_FOUND ${X11_Xtst_FOUND})
set(X11_XTest_INCLUDE_PATH "${X11_Xtst_INCLUDE_PATH}")
set(X11_XTest_LIB "${X11_Xtst_LIB}")
set(X11_Xinput_FOUND ${X11_Xi_FOUND})
set(X11_Xinput_INCLUDE_PATH "${X11_Xi_INCLUDE_PATH}")
set(X11_Xinput_LIB "${X11_Xi_LIB}")
set(X11_Xkbfile_FOUND ${X11_xkbfile_FOUND})
set(X11_Xkbfile_INCLUDE_PATH "${X11_xkbfile_INCLUDE_PATH}")
set(X11_Xkbfile_LIB "${X11_xkbfile_LIB}")
set(X11_Xscreensaver_FOUND ${X11_Xss_FOUND})
set(X11_Xscreensaver_INCLUDE_PATH "${X11_Xss_INCLUDE_PATH}")
set(X11_Xscreensaver_LIB "${X11_Xss_LIB}")
set(X11_xf86misc_FOUND ${X11_Xxf86misc_FOUND})
set(X11_xf86misc_INCLUDE_PATH "${X11_Xxf86misc_INCLUDE_PATH}")
set(X11_xf86vmode_FOUND ${X11_Xxf8vm_FOUND})
set(X11_xf86vmode_INCLUDE_PATH "${X11_Xxf8vm_INCLUDE_PATH}")
