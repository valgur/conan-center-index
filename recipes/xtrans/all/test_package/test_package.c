#define X11_t
#define TRANS_CLIENT 1

static const char *__xtransname = "_X11Trans";

#include <X11/Xtrans/Xtrans.h>
#include <X11/Xtrans/transport.c>


int main() {
    TRANS(OpenCOTSClient)("");
}
