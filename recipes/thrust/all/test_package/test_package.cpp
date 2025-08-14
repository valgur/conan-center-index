#include <thrust/functional.h>
#include <thrust/iterator/counting_iterator.h>
#include <thrust/transform_reduce.h>

#include <iostream>

struct estimate_dummy
{
  float operator()(unsigned int thread_id)
  {
    return 1.0f;
  }
};

float estimate() {
  int M = 30;
  float estimate = thrust::transform_reduce(
    thrust::counting_iterator<int>(0),
    thrust::counting_iterator<int>(M),
    estimate_dummy(),
    0.0f,
    thrust::plus<float>());
  return estimate;
}

int main()
{
  std::cout << "estimate: " << estimate() << std::endl;
}
