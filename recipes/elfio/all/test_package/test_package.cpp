
#include <cstdlib>
#include <elfio/elfio.hpp>

using namespace ELFIO;

int main() {
    // just check we can create an reader, that means the recipe works
    elfio reader;
    if (!reader.load("/does/not/exist")) {
        return EXIT_SUCCESS;
    }
    return EXIT_FAILURE;
}
