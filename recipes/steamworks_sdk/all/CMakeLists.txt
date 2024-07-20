cmake_minimum_required(VERSION 3.15)
project(glmgr CXX OBJCXX)

add_library(glmgr
    cglmbuffer.cpp
    cglmfbo.cpp
    cglmprogram.cpp
    cglmquery.cpp
    cglmtex.cpp
    dx9asmtogl2.cpp
    dxabstract.cpp
    glmgr.cpp
    glmgrbasics.cpp
    glmgrcocoa.mm
    glmgrext.cpp
    mathlite.cpp
)

target_link_libraries(glmgr
    -framework Cocoa
    -framework IOKit
    -framework OpenAL
    -framework OpenGL
)

include(GNUInstallDirs)
file(GLOB HEADERS *.h)
install(FILES ${HEADERS} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
install(TARGETS glmgr
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
