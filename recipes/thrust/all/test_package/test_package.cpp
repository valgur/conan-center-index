#ifndef __host__
#define __host__
#endif
#ifndef __device__
#define __device__
#endif
#include "test_package.cuh"

#include <iostream>

int main()
{
  std::cout << "estimate: " << estimate() << std::endl;
}
