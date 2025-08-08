#include <nvpl_sparse.h>
#include <stdio.h>

int main() {
    nvpl_sparse_handle_t handle;
    nvpl_sparse_status_t status;
    int version;
    status = nvpl_sparse_create(&handle);
    if (status != NVPL_SPARSE_STATUS_SUCCESS) {
        fprintf(stderr, "Failed to create nvpl_sparse handle: %d\n", status);
        return 1;
    }
    status = nvpl_sparse_get_version(handle, &version);
    if (status != NVPL_SPARSE_STATUS_SUCCESS) {
        fprintf(stderr, "Failed to get version: %d\n", status);
        nvpl_sparse_destroy(handle);
        return 1;
    }
    int major = version / 1000;
    int minor = version % 1000 / 100;
    int patch = version % 100;
    printf("nvpl_sparse version: %d.%d.%d\n", major, minor, patch);
    nvpl_sparse_destroy(handle);
}
