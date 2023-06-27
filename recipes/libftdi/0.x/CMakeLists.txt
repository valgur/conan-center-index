cmake_minimum_required(VERSION 3.4)
project(cmake_wrapper)

find_package(libusb-compat CONFIG REQUIRED)
find_package(Boost CONFIG REQUIRED)

link_libraries(libusb-compat::libusb-compat Boost::boost)

add_subdirectory(source_subfolder)
