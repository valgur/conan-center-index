#include <x86simdsort.h>
#include <vector>

int main() {
    std::vector<float> arr{1000};
    x86simdsort::qsort(arr.data(), 1000, true);
}
