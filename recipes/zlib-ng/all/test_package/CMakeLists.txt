cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

add_executable(${PROJECT_NAME} test_package.c)
target_compile_features(${PROJECT_NAME} PRIVATE c_std_99)

if (ZLIB_COMPAT)
  find_package(ZLIB REQUIRED)
  target_link_libraries(${PROJECT_NAME} PRIVATE ZLIB::ZLIB)
else()
  find_package(zlib-ng REQUIRED CONFIG)
  target_link_libraries(${PROJECT_NAME} PRIVATE zlib-ng::zlib)
endif()
