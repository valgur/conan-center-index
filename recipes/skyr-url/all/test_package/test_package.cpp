#include <iostream>
#include <skyr/url.hpp>

int main() {
    using namespace skyr::literals;

    auto url = "http://sub.example:8090/paths/to/a/file"_url;
    std::cout << url << std::endl;
    std::cout << url.pathname() << std::endl;
}
