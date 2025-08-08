cmake_minimum_required(VERSION 3.15)
project(sqlite3 LANGUAGES C)

add_library(sqlite3 sqlite3.c sqlite3.rc)
set_target_properties(sqlite3 PROPERTIES C_VISIBILITY_PRESET hidden)
if(BUILD_SHARED_LIBS)
    if(WIN32)
        target_compile_definitions(sqlite3 PUBLIC "SQLITE_API=__declspec(dllexport)" )
    else()
        target_compile_definitions(sqlite3 PUBLIC "SQLITE_API=__attribute__((visibility(\"default\")))" )
    endif()
endif()
target_compile_definitions(sqlite3 PRIVATE $<$<COMPILE_LANGUAGE:RC>:RC_VERONLY>)

if(THREADSAFE)
    find_package(Threads REQUIRED)
    target_link_libraries(sqlite3 PRIVATE Threads::Threads)
endif()

if(ENABLE_ICU)
    find_package(ICU REQUIRED COMPONENTS data i18n uc)
    target_link_libraries(sqlite3 PRIVATE ICU::i18n ICU::uc ICU::data)
    enable_language(CXX) # required for linking language since ICU has c++ code
endif()

if(NOT OMIT_LOAD_EXTENSION)
    target_link_libraries(sqlite3 PRIVATE ${CMAKE_DL_LIBS})
endif()

set(SQLITE3_LIBRARY_NEEDS_MATH FALSE)
if(ENABLE_FTS5 OR ENABLE_MATH_FUNCTIONS)
    set(SQLITE3_LIBRARY_NEEDS_MATH TRUE)
endif()

set(SQLITE3_EXECUTABLE_NEEDS_MATH FALSE)
if(SQLITE3_BUILD_EXECUTABLE AND SQLITE3_VERSION VERSION_GREATER_EQUAL "3.49.2")
    set(SQLITE3_EXECUTABLE_NEEDS_MATH TRUE)
endif()

set(NEED_MATH_LIBRARY FALSE)
if(SQLITE3_LIBRARY_NEEDS_MATH OR SQLITE3_EXECUTABLE_NEEDS_MATH)
    set(NEED_MATH_LIBRARY TRUE)
endif()

if(NEED_MATH_LIBRARY)
    include(CheckLibraryExists)
    # Check if math functionality is on the separate 'libm' library,
    # otherwise assume that it is already part of the C runtime.
    # The `m` library is part of the compiler toolchain, this checks
    # if the compiler can successfully link against the library.
    check_library_exists(m log "" HAVE_MATH_LIBRARY)
endif()

if(SQLITE3_LIBRARY_NEEDS_MATH AND HAVE_MATH_LIBRARY)
    target_link_libraries(sqlite3 PUBLIC m)
endif()

install(TARGETS sqlite3
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)
install(FILES sqlite3.h sqlite3ext.h DESTINATION include)

if(SQLITE3_BUILD_EXECUTABLE)
    add_executable(sqlite3-bin shell.c)
    target_link_libraries(sqlite3-bin PRIVATE sqlite3)
    if(SQLITE3_EXECUTABLE_NEEDS_MATH AND HAVE_MATH_LIBRARY)
        target_link_libraries(sqlite3-bin PRIVATE m)
    endif()
    if(ENABLE_DBPAGE_VTAB)
        target_compile_definitions(sqlite3-bin PRIVATE SQLITE_ENABLE_DBPAGE_VTAB)
    endif()
    if(ENABLE_ICU)
        set_target_properties(sqlite3-bin PROPERTIES LINKER_LANGUAGE CXX)
    endif()
    if (MSVC)
        # Prevent issue where an import library may be generated on Windows
        #  fatal error LNK1149: output filename matches input filename '\build\Release\sqlite3.lib'\
        target_link_options(sqlite3-bin PRIVATE "/noimplib")
    endif()
    set_target_properties(sqlite3-bin PROPERTIES OUTPUT_NAME "sqlite3" PDB_NAME "sqlite3-bin")
    include(CheckSymbolExists)
    check_symbol_exists(system "stdlib.h" HAVE_SYSTEM)
    if(NOT HAVE_SYSTEM)
        target_compile_definitions(sqlite3-bin PRIVATE SQLITE_NOHAVE_SYSTEM)
    endif()
    install(TARGETS sqlite3-bin DESTINATION bin)
endif()
