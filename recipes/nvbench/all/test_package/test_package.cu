#include <nvbench/nvbench.cuh>

void bench(nvbench::state &state)
{
  state.add_element_count(64, "Items");
}
NVBENCH_BENCH(bench);
