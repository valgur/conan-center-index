#include "CDSPResampler.h"
#include "r8bbase.h"

int main() { r8b::CDSPResampler24 resampler(44100.0f, 48000.0f, 512); }
