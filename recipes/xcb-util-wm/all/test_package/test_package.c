#include <xcb/xcb_ewmh.h>
#include <xcb/xcb_icccm.h>

#include <stddef.h>

void dummy() {
    xcb_ewmh_init_atoms(NULL, NULL);
    xcb_icccm_get_wm_protocols_reply_wipe(NULL);
}

int main() {
}
