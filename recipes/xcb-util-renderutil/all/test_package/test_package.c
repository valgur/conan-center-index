#include <xcb/xcb_renderutil.h>

int main() {
    xcb_render_glyphset_t glyphset = 0;
    xcb_render_util_composite_text_stream(glyphset, 0, 0);
}
