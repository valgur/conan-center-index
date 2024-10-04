#include <xcb/xcb.h>

int main() {
    int screen = 0;
    xcb_connect("", &screen);
}
