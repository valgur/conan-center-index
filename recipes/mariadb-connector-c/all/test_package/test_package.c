#include <mysql.h>
#include <stdio.h>

// See #4530
#include <mysqld_error.h>

int main() {
    printf("MySQL client version: %s\n", mysql_get_client_info());
    printf("MARIADB_PLUGINDIR: %s\n", MARIADB_PLUGINDIR);

    return 0;
}
