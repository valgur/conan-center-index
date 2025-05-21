#include <libunwind.h>

int main() {
    unw_context_t uc;
    unw_getcontext(&uc);
}
