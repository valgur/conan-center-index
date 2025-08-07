#include <cuda.h>
#include <nvshmem.h>

void dummy() {
    cudaStream_t stream;
    nvshmem_init();
    int mype_node = nvshmem_team_my_pe(NVSHMEMX_TEAM_NODE);
    cudaSetDevice(mype_node);
    cudaStreamCreate(&stream);
    nvshmemx_barrier_all_on_stream(stream);
    cudaStreamSynchronize(stream);
    nvshmem_finalize();
}

int main() { }
