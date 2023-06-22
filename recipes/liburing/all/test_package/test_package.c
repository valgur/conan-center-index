#include "liburing.h"

const unsigned entries = 5;

int main() {
    struct io_uring ring;
    int ret = io_uring_queue_init(entries, &ring, 0);
    if (ret < 0) {
        return -ret;
    }

    io_uring_queue_exit(&ring);
    return 0;
}
