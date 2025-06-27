#include <cppad/cppad.hpp>
#include <vector>

int main() {
   using namespace CppAD;
   size_t n = 1;
   std::vector<AD<double>> ax(n);
   ax[0] = 3.;
   CppAD::Independent(ax);
}
