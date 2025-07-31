#include <upa/url.h>
#include <iostream>

int main() {
    upa::url url{ "https://upa-url.github.io/docs/", "about:blank" };
    std::cout << url.href() << '\n';
}
