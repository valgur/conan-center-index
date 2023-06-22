#include <iostream>
#include <qpdf/DLL.h>
#include <qpdf/QPDF.hh>
#include <qpdf/QPDFWriter.hh>

int main() {
    std::cout << "QPDF_VERSION " << QPDF_VERSION << "\n";

    try {
        QPDF pdf;
        pdf.emptyPDF();
        QPDFWriter w(pdf, "empty_example.pdf");
        w.write();
    } catch (std::exception &e) {
        std::cerr << e.what() << "\n";
        exit(2);
    }

    return 0;
}
