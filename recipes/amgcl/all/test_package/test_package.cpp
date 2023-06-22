#include <amgcl/profiler.hpp>
#include <cstdlib>

int main() {
    amgcl::profiler<> profile;
    profile.tic("assemble");

    return EXIT_SUCCESS;
}
