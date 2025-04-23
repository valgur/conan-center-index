#include <khash.h>

KHASH_MAP_INIT_INT(m32, char)
int main() {
    khash_t(m32) *h = kh_init(m32);
}
