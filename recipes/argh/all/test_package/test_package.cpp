#include <argh.h>
#include <cstdlib>
#include <iostream>

int main(int, char *argv[]) { // if this works, the package works
    argh::parser cmdl(argv);

    if (cmdl[{"-v", "--verbose"}])
        std::cout << "Working.\n";

    return EXIT_SUCCESS;
}
