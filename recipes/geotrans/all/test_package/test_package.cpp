#include <geotrans/GeodeticParameters.h>
#include <geotrans/CoordinateType.h>
#include <geotrans/HeightType.h>

int main()
{
    MSP::CCS::GeodeticParameters ellipsoidParameters(
        MSP::CCS::CoordinateType::geodetic,
        MSP::CCS::HeightType::ellipsoidHeight);
}
