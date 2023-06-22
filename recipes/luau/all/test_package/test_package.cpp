#include "lua.h"
#include "lualib.h"

#include <string>

int main() {
    lua_State *L = luaL_newstate();
    lua_close(L);
    return 0;
}
