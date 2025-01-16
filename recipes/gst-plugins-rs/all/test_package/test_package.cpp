#include <gst/gst.h>
#include <gst/gstplugin.h>

#ifdef GST_PLUGINS_BASE_STATIC

extern "C"
{
    GST_PLUGIN_STATIC_DECLARE(rswebrtc);
}

#endif

#include <iostream>

int main(int argc, char * argv[])
{
    gst_init(&argc, &argv);

#ifdef GST_PLUGINS_BASE_STATIC

    GST_PLUGIN_STATIC_REGISTER(rswebrtc);

#endif

    GstElement * rswebrtc = gst_element_factory_make("rswebrtc", NULL);
    if (!rswebrtc) {
        std::cerr << "failed to create rswebrtc element" << std::endl;
        return -1;
    } else {
        std::cout << "rswebrtc has been created successfully" << std::endl;
    }
    gst_object_unref(GST_OBJECT(rswebrtc));
    return 0;
}
