#include <xcb/xcb_image.h>

#include <stdlib.h>

int main() {
    xcb_image_t *image = malloc(sizeof(xcb_image_t));
    xcb_image_destroy(image);
}
