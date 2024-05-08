#include <stdint.h>

#include <semphr.h>

#include <FreeRTOS.h>

volatile uint32_t task_status_ticks = 0;

void vApplicationTickHook(void) { return; }

void vApplicationMallocFailedHook(void)
{
    for ( ;; )
    {
    }
}

void vApplicationIdleHook(void) {}

void vApplicationDaemonTaskStartupHook(void) {}

void vApplicationStackOverflowHook(TaskHandle_t pxTask, char *pcTaskName)
{
    (void)pcTaskName;
    (void)pxTask;

    taskDISABLE_INTERRUPTS();
    for ( ;; )
    {
    }
}

void HardFault_Handler(void)
{
    for ( ;; )
    {
    }
}

//==============================================================================
int main()
{
    SemaphoreHandle_t semPtr = xSemaphoreCreateBinary();
    return 0;
}
