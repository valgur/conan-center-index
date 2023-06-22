#include <uchardet/uchardet.h>

int main() {
    auto ud = uchardet_new();
    uchardet_delete(ud);
    return 0;
}
