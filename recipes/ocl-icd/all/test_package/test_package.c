#include <ocl_icd.h>

CL_API_ENTRY cl_int CL_API_CALL clIcdGetPlatformIDsKHR(
             cl_uint num_entries,
             cl_platform_id *platforms,
             cl_uint *num_platforms) {
  if( platforms == NULL && num_platforms == NULL )
    return CL_INVALID_VALUE;
  if( num_entries == 0 && platforms != NULL )
    return CL_INVALID_VALUE;
  return CL_SUCCESS;
}

int main() { }
