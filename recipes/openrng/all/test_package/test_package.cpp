#include <openrng.h>

int main() {
  VSLStreamStatePtr stream;
  int errcode = vslNewStream(&stream, VSL_BRNG_PHILOX4X32X10, 42);
}
