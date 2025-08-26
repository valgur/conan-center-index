#include <cudf/io/csv.hpp>
#include <cudf/table/table.hpp>
#include <iostream>

int main() {
    std::string csv =
        "id,name,age\n"
        "1,Alice,30\n"
        "2,Bob,25\n";
    auto src = cudf::io::source_info{ cudf::host_span<char const>(csv.data(), csv.size()) };
    auto opts = cudf::io::csv_reader_options::builder(src)
        .compression(cudf::io::compression_type::NONE)
        .header(0)
        .build();
    // Skipping the actual read since it requires a GPU to run on.
    if (false) {
        auto result = cudf::io::read_csv(opts);
        std::cout << result.tbl->num_columns() << " "
                  << result.tbl->num_rows() << "\n";
    }
}
