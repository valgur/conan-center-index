#include <cppad/cg.hpp>
#include <vector>

int main() {
    using namespace CppAD;
    using namespace CppAD::cg;
    typedef CG<double> CGD;
    typedef AD<CGD> ADCG;
    std::vector<ADCG> x(2);
    Independent(x);
}
