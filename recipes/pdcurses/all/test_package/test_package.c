#include "curses.h"

#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("PDCurses version %s\n", curses_version());
    return EXIT_SUCCESS;
}
