
#if defined COMPILE_AS_CPP
#include "lauxlib.h"
#include "lua.h"
#include "lualib.h"
#else
#include "lua.hpp"
#endif
#include <string>

int main() {
    lua_State *L = luaL_newstate();
    luaL_dostring(L, "x = 47");
    lua_getglobal(L, "x");
    lua_Number x = lua_tonumber(L, 1);
    printf("lua says x = %d\n", (int)x);
    lua_close(L);
    return 0;
}
