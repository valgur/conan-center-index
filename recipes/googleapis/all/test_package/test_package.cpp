#include <google/bigtable/v2/bigtable.pb.h>
#include <iostream>

int main() {
    std::cout << "Conan - test package for googleapis\n";

    google::bigtable::v2::CheckAndMutateRowRequest request;
    request.set_table_name("projects/my-project/instances/my-instance/tables/my-table");

    std::cout << request.DebugString();

    return 0;
}
