#include <ShaderConductor/ShaderConductor.hpp>
#include <iostream>

int main() {
    bool link_support = ShaderConductor::Compiler::LinkSupport();
    std::cout << "Compiler::LinkSupport(): " << (link_support ? "true" : "false") << std::endl;
}
