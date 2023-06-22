#define PICOBENCH_DEBUG
#define PICOBENCH_IMPLEMENT_WITH_MAIN
#include "picobench/picobench.hpp"

#include <cstdlib>
#include <deque>
#include <vector>

void rand_vector(picobench::state &s) {
    std::vector<int> v;
    for (auto _ : s) {
        v.push_back(rand());
    }
}
PICOBENCH(rand_vector);

void rand_vector_reserve(picobench::state &s) {
    std::vector<int> v;
    v.reserve(s.iterations());
    for (auto _ : s) {
        v.push_back(rand());
    }
}
PICOBENCH(rand_vector_reserve);

void rand_deque(picobench::state &s) {
    std::deque<int> v;
    for (auto _ : s) {
        v.push_back(rand());
    }
}
PICOBENCH(rand_deque);
