#include <ncurses.h>

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int ret = EXIT_SUCCESS;
    initscr();
    addstr("Hello World");
    refresh();
    if (curscr == (void *)0) {
        ret = EXIT_FAILURE;
    }
    endwin();
    printf("ncurses version '%s'\n", curses_version());
    return ret;
}
