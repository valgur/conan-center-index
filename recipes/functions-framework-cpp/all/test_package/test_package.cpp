#include <google/cloud/functions/framework.h>
#include <iostream>

int main() {
    std::cout << google::cloud::functions::VersionString() << "\n";
    return 0;
}
