#include <nvpl_scalapack.h>

int main() {
    nvpl_int_t ic = -1, what = 0, icontxt = 0;
    Cblacs_get(ic, what, &icontxt);
}
