#include <ucp/api/ucp.h>
#include <stdio.h>

int main() {
    printf("UCX version: %s\n", ucp_get_version_string());
}
