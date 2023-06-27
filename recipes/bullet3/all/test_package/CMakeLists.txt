cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Bullet REQUIRED CONFIG)
include(${BULLET_ROOT_DIR}/${BULLET_USE_FILE})

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} ${BULLET_LIBRARIES})
target_compile_features(${PROJECT_NAME} PRIVATE cxx_std_11)
