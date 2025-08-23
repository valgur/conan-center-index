cmake_minimum_required(VERSION 3.15)
project(cocoapi C)

add_library(cocoapi common/maskApi.c)

install(TARGETS cocoapi
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(FILES common/maskApi.h DESTINATION include)
