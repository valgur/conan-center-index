#include <steam/steam_api.h>

#include <stdio.h>

int main() {
    SteamErrMsg errMsg = {0};
    SteamAPI_InitEx(&errMsg);
    printf("SteamAPI_InitEx: %s\n", errMsg);
    SteamAPI_Shutdown();
}
