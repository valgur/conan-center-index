#include <stablehlo/api/PortableApi.h>
#include <iostream>

int main() {
    std::cout << "StableHLO version: " << mlir::stablehlo::getCurrentVersion() << std::endl;
}
