#include <liblas/liblas.hpp>
#include <iostream>

int main() {
    using namespace liblas;
    std::cout << "IsGDALEnabled(): " << IsGDALEnabled() << std::endl;
    std::cout << "IsLibGeoTIFFEnabled(): " << IsLibGeoTIFFEnabled() << std::endl;
    std::cout << "IsLasZipEnabled(): " << IsLibGeoTIFFEnabled() << std::endl;
}
