#include <vips/vips.h>

int main(int argc, char **argv) {
    if (VIPS_INIT(argv[0])) {
        vips_error_exit(NULL);
    }
}
