#include <cuco/static_set.cuh>

int dummy_main() {
  cuco::static_set<int> set{cuco::extent<std::size_t>{40}, cuco::empty_key{-1}};
}

int main() {
}
