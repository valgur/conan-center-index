#include <QArchive>

int main() {
    QArchive::DiskExtractor Extractor("Test.7z");

    Extractor.start();
    Extractor.cancel();

    return 0;
}
