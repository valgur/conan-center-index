cmake_minimum_required(VERSION 3.15)
project(TestPackage CXX)

find_package(packio REQUIRED CONFIG)

if (PACKIO_VERSION VERSION_LESS "1.2.0")
    add_executable(main 1.0.x-1.1.x.cpp)
elseif (PACKIO_VERSION VERSION_LESS "2.0.0")
    add_executable(main 1.2.x.cpp)
else ()
    add_executable(main latest.cpp)
endif ()

target_link_libraries(main PRIVATE packio::packio)
set_property(TARGET main PROPERTY CXX_STANDARD 17)
