#include <h5pp/h5pp.h>

int main() {
    std::string outputFilename = "test_package.h5";
    size_t      logLevel       = 1;
    h5pp::File  file(outputFilename, H5F_ACC_TRUNC | H5F_ACC_RDWR, logLevel);

#if defined(H5PP_USE_FLOAT128)
    __float128 f128 = 6.28318530717958623199592693708837032318115234375;
    file.writeDataset(f128, "__float128");
    auto f128_read = file.readDataset<__float128>("__float128");
#endif
}
