//
// Timer.cpp
//
// This sample demonstrates the Timer and Stopwatch classes.
//
// Copyright (c) 2004-2006, Applied Informatics Software Engineering GmbH.
// and Contributors.
//
// SPDX-License-Identifier:	BSL-1.0
//

#include "Poco/Stopwatch.h"
#include "Poco/Thread.h"
#include "Poco/Timer.h"
#include <iostream>

using Poco::Stopwatch;
using Poco::Thread;
using Poco::Timer;
using Poco::TimerCallback;

class TimerExample {
  public:
    TimerExample() { _sw.start(); }

    void onTimer(Timer &timer) {
        std::cout << "Callback called after " << _sw.elapsed() / 1000 << " milliseconds."
                  << std::endl;
    }

  private:
    Stopwatch _sw;
};

int main() {
    TimerExample example;

    Timer timer(25, 50);
    timer.start(TimerCallback<TimerExample>(example, &TimerExample::onTimer));

    Thread::sleep(500);

    timer.stop();

    return 0;
}
