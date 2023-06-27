#include <OGRE/OgreParticle.h>
#include <OGRE/OgrePrerequisites.h>
#include <OGRE/OgreRenderSystemCapabilities.h>
#include <iostream>

int main() {
    Ogre::RenderSystemCapabilities rc;
    rc.setNumTextureUnits(10);
    std::cout << "Hello from OgreMain component\n";
    std::cout << "number of texture units: " << rc.getNumTextureUnits() << "\n";

    Ogre::Radian rot{0.618};
    Ogre::Particle particle;
    particle.resetDimensions();

    return 0;
}
