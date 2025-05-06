#include <google/bigtable/v2/bigtable.pb.h>
#include <iostream>

int main() {
    google::bigtable::v2::CheckAndMutateRowRequest request;
    request.set_table_name("projects/my-project/instances/my-instance/tables/my-table");
    std::cout << request.DebugString();
}
