#include <armpl.h>
#include <fftw3.h>

int main() {
	fftw_complex in[1000] = {0};
	double out[1000] = {0};
	fftw_plan plan = fftw_plan_dft_c2r_1d(sizeof(in), in, out, FFTW_ESTIMATE);
	fftw_execute(plan);
}
