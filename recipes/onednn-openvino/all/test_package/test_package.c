#include <dnnl.h>

int main() {
    dnnl_set_max_cpu_isa(dnnl_cpu_isa_avx);
}
