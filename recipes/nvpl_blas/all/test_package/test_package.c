#include <nvpl_blas.h>
#include <stdio.h>

int main() {
    const nvpl_int_t N = 5;
    const nvpl_int_t incX = 1;
    float X[5] = {1.0f, -2.0f, 3.0f, -4.0f, 5.0f};
    float result;
    result = cblas_sasum(N, X, incX);
    printf("The sum of absolute values is: %f\n", result);
}
