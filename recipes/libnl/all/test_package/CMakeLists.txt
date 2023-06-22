cmake_minimum_required(VERSION 3.15)
project(netlink_example LANGUAGES C)

find_package(libnl REQUIRED CONFIG)

add_executable(show_links show_links.c)
target_link_libraries(show_links libnl::libnl)
