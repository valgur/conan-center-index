#include <stdlib.h>

#include <libwacom/libwacom.h>

int main(void) {
    char* datadir = getenv("LIBWACOM_DATA_DIR");
    if (!datadir) {
        return EXIT_FAILURE;
    }
    WacomDeviceDatabase *db = libwacom_database_new_for_path(datadir);
    if (!db) {
      return EXIT_FAILURE;
    }
    libwacom_database_destroy(db);
    return EXIT_SUCCESS;
}
