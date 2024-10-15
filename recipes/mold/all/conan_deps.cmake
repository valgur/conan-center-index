find_package(zstd REQUIRED CONFIG)
link_libraries(zstd::zstd)
find_package(xxHash REQUIRED CONFIG)
link_libraries(xxHash::xxhash)
