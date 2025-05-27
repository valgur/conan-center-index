#include <ufbx.h>
#include <stddef.h>

int main() {
    ufbx_load_opts opts = { 0 };
    ufbx_scene *scene = ufbx_load_memory(NULL, 0, &opts, NULL);
    ufbx_free_scene(scene);
}
