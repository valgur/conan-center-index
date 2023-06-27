#include <iostream>
#include <toml.hpp>

int main() {
    std::stringstream sstr;
    sstr << "title = 'an example toml file'";
    const auto data = toml::parse(sstr);

    std::string title = toml::find<std::string>(data, "title");
    std::cout << "the title is " << title << std::endl;

    return 0;
}
