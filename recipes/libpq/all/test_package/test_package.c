#include "libpq-fe.h"

#include <stdio.h>
#include <stdlib.h>

int main() {
    PGconn *conn = NULL;
    const int version = PQlibVersion();
    printf("PQlibVersion: %d\n", version);

    conn = PQconnectdb("dbname = postgres");
    PQstatus(conn);

    PQfinish(conn);
    return EXIT_SUCCESS;
}
