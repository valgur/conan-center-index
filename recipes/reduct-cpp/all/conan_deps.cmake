find_package(fmt REQUIRED CONFIG)
find_package(httplib REQUIRED CONFIG)
find_package(nlohmann_json REQUIRED CONFIG)
find_package(OpenSSL REQUIRED CONFIG)
find_package(concurrentqueue REQUIRED CONFIG)
find_package(date REQUIRED CONFIG)

add_library(dependencies INTERFACE)
target_link_libraries(dependencies INTERFACE
    fmt::fmt
    nlohmann_json::nlohmann_json
    httplib::httplib
    concurrentqueue::concurrentqueue
    date::date
)
