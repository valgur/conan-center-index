#include "dap/dap.h"
#include <cstdlib>

int main() {

    dap::initialize();
    dap::terminate();

    return EXIT_SUCCESS;
}
