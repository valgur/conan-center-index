cmake_minimum_required(VERSION 3.15)
project(MoltenVK)

if(NOT (CMAKE_SYSTEM_NAME STREQUAL "Darwin" OR
        CMAKE_SYSTEM_NAME STREQUAL "iOS" OR
        CMAKE_SYSTEM_NAME STREQUAL "tvOS"))
    message(FATAL_ERROR "MoltenVK only supports MacOS, iOS and tvOS")
endif()

option(MVK_WITH_SPIRV_TOOLS "Build MoltenVK without the MVK_EXCLUDE_SPIRV_TOOLS build setting" ON)
option(MVK_BUILD_SHADERCONVERTER_TOOL "Build MoltenVKShaderConverter" ON)
if(BUILD_SHARED_LIBS)
    option(MVK_HIDE_VULKAN_SYMBOLS "Hide Vulkan symbols" OFF)
endif()

set(MVK_INSTALL_TARGETS "")

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/bin)

# PIC required for objects targets linked into shared MoltenVK
if(BUILD_SHARED_LIBS)
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)
endif()

find_package(cereal REQUIRED CONFIG)
find_package(glslang REQUIRED glslang SPIRV CONFIG)
find_package(spirv-cross REQUIRED CONFIG)
find_package(VulkanHeaders REQUIRED CONFIG)
if(MVK_WITH_SPIRV_TOOLS)
    find_package(SPIRV-Tools REQUIRED CONFIG)
endif()

# Find mandatory Apple Frameworks
function(find_library_required foundVar framework)
    find_library(${foundVar} ${framework})
    if(NOT ${foundVar})
        message(FATAL_ERROR "${framework} framework not found")
    endif()
endfunction()

find_library_required(METAL_FRAMEWORK Metal)
find_library_required(FOUNDATION_FRAMEWORK Foundation)
find_library_required(QUARTZCORE_FRAMEWORK QuartzCore)
find_library_required(IOSURFACE_FRAMEWORK IOSurface)
find_library_required(COREGRAPHICS_FRAMEWORK CoreGraphics)
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    find_library_required(APPKIT_FRAMEWORK AppKit)
    find_library_required(IOKIT_FRAMEWORK IOKit)
else()
    find_library_required(UIKIT_FRAMEWORK UIKit)
endif()

add_compile_options(
    -Wno-unguarded-availability-new
    -Wno-deprecated-declarations
    -Wno-nonportable-include-path
    -Wno-tautological-pointer-compare
    -Wno-non-c-typedef-for-linkage
    -Wno-switch
)

# MoltenVKCommon
file(GLOB MVK_COMMON_SOURCES common/*.mm)
add_library(MoltenVKCommon OBJECT ${MVK_COMMON_SOURCES})
target_include_directories(MoltenVKCommon PUBLIC common)
target_compile_definitions(MoltenVKCommon PRIVATE $<$<CONFIG:Debug>:DEBUG=1>)
target_link_libraries(MoltenVKCommon PRIVATE ${FOUNDATION_FRAMEWORK})
if(BUILD_SHARED_LIBS)
    set_target_properties(MoltenVKCommon PROPERTIES
        C_VISIBILITY_PRESET hidden
        OBJC_VISIBILITY_PRESET hidden
        CXX_VISIBILITY_PRESET hidden
        OBJCXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )
endif()

# MoltenVKShaderConverter
file(GLOB MVK_SC_SOURCES
    MoltenVKShaderConverter/MoltenVKShaderConverter/*.cpp
    MoltenVKShaderConverter/MoltenVKShaderConverter/*.mm
)
add_library(MoltenVKShaderConverter OBJECT ${MVK_SC_SOURCES})
target_compile_features(MoltenVKShaderConverter PUBLIC cxx_std_17)
target_include_directories(MoltenVKShaderConverter INTERFACE MoltenVKShaderConverter)
target_link_libraries(MoltenVKShaderConverter
    PRIVATE
        glslang::glslang
        glslang::SPIRV
        MoltenVKCommon
        $<$<BOOL:${MVK_WITH_SPIRV_TOOLS}>:SPIRV-Tools>
        ${FOUNDATION_FRAMEWORK}
    PUBLIC
        spirv-cross-core
        spirv-cross-msl
        spirv-cross-reflect
)
target_compile_definitions(MoltenVKShaderConverter PRIVATE
    $<$<NOT:$<BOOL:${MVK_WITH_SPIRV_TOOLS}>>:MVK_EXCLUDE_SPIRV_TOOLS>
)
if(BUILD_SHARED_LIBS)
    set_target_properties(MoltenVKShaderConverter PROPERTIES
        C_VISIBILITY_PRESET hidden
        OBJC_VISIBILITY_PRESET hidden
        CXX_VISIBILITY_PRESET hidden
        OBJCXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )
endif()

# MoltenVKShaderConverterTool
if(MVK_BUILD_SHADERCONVERTER_TOOL)
    file(GLOB MVK_SCT_SOURCES
        MoltenVKShaderConverter/MoltenVKShaderConverterTool/*.cpp
        MoltenVKShaderConverter/MoltenVKShaderConverterTool/*.mm
    )
    add_executable(MoltenVKShaderConverterTool ${MVK_SCT_SOURCES})
    target_compile_features(MoltenVKShaderConverterTool PUBLIC cxx_std_17)
    set_property(TARGET MoltenVKShaderConverterTool PROPERTY OUTPUT_NAME MoltenVKShaderConverter)
    target_include_directories(MoltenVKShaderConverterTool PRIVATE
        MoltenVKShaderConverter/MoltenVKShaderConverter
    )
    target_link_libraries(MoltenVKShaderConverterTool PRIVATE
        MoltenVKCommon
        MoltenVKShaderConverter
        ${METAL_FRAMEWORK}
        ${FOUNDATION_FRAMEWORK}
    )
    list(APPEND MVK_INSTALL_TARGETS MoltenVKShaderConverterTool)
endif()

# MoltenVK
file(GLOB_RECURSE MVK_SOURCES
    MoltenVK/MoltenVK/*.m
    MoltenVK/MoltenVK/*.mm
    MoltenVK/MoltenVK/*.cpp
)
add_library(MoltenVK ${MVK_SOURCES})
target_compile_features(MoltenVK PUBLIC cxx_std_17)
target_include_directories(MoltenVK PRIVATE
    MoltenVK/MoltenVK/API
    MoltenVK/MoltenVK/Commands
    MoltenVK/MoltenVK/GPUObjects
    MoltenVK/MoltenVK/Layers
    MoltenVK/MoltenVK/OS
    MoltenVK/MoltenVK/Utility
    MoltenVK/MoltenVK/Vulkan
)
target_link_libraries(MoltenVK
    PRIVATE
        cereal
        MoltenVKCommon
        MoltenVKShaderConverter
        ${FOUNDATION_FRAMEWORK}
        ${QUARTZCORE_FRAMEWORK}
        $<$<PLATFORM_ID:Darwin>:${APPKIT_FRAMEWORK}>
        $<$<PLATFORM_ID:Darwin>:${IOKIT_FRAMEWORK}>
        $<$<NOT:$<PLATFORM_ID:Darwin>>:${UIKIT_FRAMEWORK}>
    PUBLIC
        Vulkan::Headers
        ${METAL_FRAMEWORK}
        ${IOSURFACE_FRAMEWORK}
        ${COREGRAPHICS_FRAMEWORK}
)
if(BUILD_SHARED_LIBS)
    set_target_properties(MoltenVK PROPERTIES
        C_VISIBILITY_PRESET hidden
        OBJC_VISIBILITY_PRESET hidden
        CXX_VISIBILITY_PRESET hidden
        OBJCXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )
    if(MVK_HIDE_VULKAN_SYMBOLS)
        target_compile_definitions(MoltenVK PRIVATE MVK_HIDE_VULKAN_SYMBOLS)
    endif()
endif()
list(APPEND MVK_INSTALL_TARGETS MoltenVK)

# Custom Target to generate internal header file required by MoltenVK target.
# This header should contain:
#  - if moltenvk < 1.0.44 : spirv-cross commit hash in spirvCrossRevisionString variable
#  - if moltenvk >= 1.0.44: moltenvk commit hash in mvkRevString variable (but we still
#    use spirv-cross commit hash, since MoltenVK hash is not available in this context,
#    and hash value is no really important)
set(MVK_REV_FILE ExternalRevisions/SPIRV-Cross_repo_revision)
set(MVK_REV_HEADER_DIR ${CMAKE_CURRENT_BINARY_DIR}/mvk_hash_generated)
set(MVK_REV_HEADER ${MVK_REV_HEADER_DIR}/mvkGitRevDerived.h)
set(MVK_REV_VAR_NAME mvkRevString)
set(MVK_REV_DEFINES -DMVK_REV_FILE=${MVK_REV_FILE} -DMVK_REV_HEADER=${MVK_REV_HEADER} -DMVK_REV_VAR_NAME=${MVK_REV_VAR_NAME})
set(MVK_REV_GEN_SCRIPT "${CMAKE_CURRENT_BINARY_DIR}/mvk_git_hash_generator.cmake")
file(WRITE ${MVK_REV_GEN_SCRIPT}
    "file(READ \${MVK_REV_FILE} MVK_SPIRV_CROSS_GIT_REV)\n"
    "string(REPLACE \"\\n\" \"\" MVK_SPIRV_CROSS_GIT_REV \${MVK_SPIRV_CROSS_GIT_REV})\n"
    "file(WRITE \${MVK_REV_HEADER} \"static const char* \${MVK_REV_VAR_NAME} = \\\"\${MVK_SPIRV_CROSS_GIT_REV}\\\";\")\n"
)
add_custom_target(mvk-commit-hash-header DEPENDS ${MVK_REV_HEADER})
add_custom_command(
    COMMENT "Create ${MVK_REV_HEADER}"
    OUTPUT ${MVK_REV_HEADER}
    DEPENDS ${MVK_REV_FILE}
    COMMAND ${CMAKE_COMMAND} ${MVK_REV_DEFINES} -P ${MVK_REV_GEN_SCRIPT}
)
add_dependencies(MoltenVK mvk-commit-hash-header)
target_include_directories(MoltenVK PRIVATE ${MVK_REV_HEADER_DIR})

# Installation
install(
    TARGETS ${MVK_INSTALL_TARGETS}
    BUNDLE DESTINATION ${CMAKE_INSTALL_BINDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

if(BUILD_SHARED_LIBS)
    install(
        FILES MoltenVK/icd/MoltenVK_icd.json
        DESTINATION ${CMAKE_INSTALL_LIBDIR}
    )
endif()

file(GLOB MVK_PUBLIC_HEADERS MoltenVK/MoltenVK/API/*.h)
install(
    FILES ${MVK_PUBLIC_HEADERS}
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/MoltenVK
)

file(GLOB MVK_SC_PUBLIC_HEADERS
    MoltenVKShaderConverter/MoltenVKShaderConverter/*Conversion.h
    MoltenVKShaderConverter/MoltenVKShaderConverter/*Converter.h
)
install(
    FILES ${MVK_SC_PUBLIC_HEADERS}
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/MoltenVKShaderConverter
)
