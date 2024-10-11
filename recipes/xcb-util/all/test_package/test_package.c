#include <xcb/xcb_util.h>

#include <stdio.h>

int main() {
    char *color = "cornflower blue";
    uint16_t r, g, b;
    xcb_aux_parse_color(color, &r, &g, &b);
    printf("%s -> R: %d, G: %d, B: %d\n", color, r / 256, g / 256, b / 256);
}
