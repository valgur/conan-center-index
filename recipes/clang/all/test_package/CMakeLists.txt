cmake_minimum_required(VERSION 3.15)

project(test_package LANGUAGES CXX)

find_package(Clang REQUIRED CONFIG)
add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} PRIVATE clangTooling)

# See https://clang.llvm.org/docs/LibTooling.html#builtin-includes for explanation of the following
set(clang_include_path "lib/clang/${Clang_VERSION_MAJOR}/include")
set(clang_include_src_path "${Clang_INCLUDE_DIR}/../${clang_include_path}/")
set(clang_include_dest_path "$<TARGET_FILE_DIR:test_package>/../${clang_include_path}")

add_custom_command(
    TARGET ${PROJECT_NAME} POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${clang_include_src_path} ${clang_include_dest_path}
)
