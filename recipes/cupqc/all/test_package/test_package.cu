#include <cuhash.hpp>

using namespace cupqc;

using SHA3_256_WARP = decltype(SHA3_256() + Warp());

int main() {
    SHA3_256_WARP hash{};
}
