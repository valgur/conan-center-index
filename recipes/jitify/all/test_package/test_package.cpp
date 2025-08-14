#include <jitify.hpp>

int dummy_main() {
    const char* program_source = "my_program\n"
        "template<int N, typename T>\n"
        "__global__\n"
        "void my_kernel(T* data) {\n"
        "    T data0 = data[0];\n"
        "    for( int i=0; i<N-1; ++i ) {\n"
        "        data[0] *= data0;\n"
        "    }\n"
        "}\n";
    static jitify::JitCache kernel_cache;
    jitify::Program program = kernel_cache.program(program_source);
    int data[] = { 1, 2, 3 };
    dim3 grid(1);
    dim3 block(1);
    using jitify::reflection::type_of;
    program.kernel("my_kernel")
           .instantiate(3, type_of(*data))
           .configure(grid, block)
           .launch(data);
}

int main() { }
