cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(ValiJSON REQUIRED CONFIG)
find_package(nlohmann_json REQUIRED CONFIG)
find_package(picojson REQUIRED CONFIG)
find_package(RapidJSON REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(
    ${PROJECT_NAME}
    PRIVATE
    valijson
    nlohmann_json::nlohmann_json
    picojson::picojson
    rapidjson
)
