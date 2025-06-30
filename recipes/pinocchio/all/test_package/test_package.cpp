#include <pinocchio/utils/file-explorer.hpp>
#include <pinocchio/math/matrix.hpp>
#include <pinocchio/fwd.hpp>
#include <vector>
#include <string>

int main()
{
   std::vector<std::string> paths;
   pinocchio::extractPathFromEnvVar("XYZ", paths, ":");
}
