#include <dtl/dtl.hpp>
#include <string>

int main() {
    std::string a = "abc";
    std::string b = "abd";
    dtl::Diff<char, std::string> diff(a, b);
    diff.compose();
}
