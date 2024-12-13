cmake_minimum_required(VERSION 3.15)
project(wuffs LANGUAGES C)

add_library(wuffs release/c/wuffs-v${API_VERSION}.c)
target_compile_definitions(wuffs PRIVATE WUFFS_IMPLEMENTATION)

install(TARGETS wuffs
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)

install(FILES release/c/wuffs-v${API_VERSION}.c DESTINATION include)
