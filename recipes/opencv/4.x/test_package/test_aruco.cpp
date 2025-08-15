#include <opencv2/aruco.hpp>

int main() {
    auto dictionary = cv::aruco::getPredefinedDictionary(cv::aruco::DICT_6X6_250);
    cv::aruco::CharucoBoard board(cv::Size(5, 7), 0.04f, 0.02f, dictionary);
    cv::aruco::testCharucoCornersCollinear(&board, cv::Mat::ones(4, 6, CV_32SC1));
}
