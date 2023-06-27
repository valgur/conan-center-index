#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#ifndef _WIN32
#include <netinet/in.h>
#ifdef _XOPEN_SOURCE_EXTENDED
#include <arpa/inet.h>
#endif
#include <sys/socket.h>
#endif

#include <event2/buffer.h>
#include <event2/bufferevent.h>
#include <event2/event.h>
#include <event2/listener.h>
#include <event2/util.h>

int main() {
    struct event_base *base;
    const char *version = event_get_version();

    base = event_base_new();
    if (!base) {
        fprintf(stderr, "Could not initialize libevent!\n");
        return 1;
    }

    event_base_free(base);

    printf("Version %s\n", version);
    printf("done\n");
    return 0;
}
