#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include "pinout.h"
#include <stdio.h>

static const char *TAG = "AgroAgent";

// Prototipos de funciones de inicialización
void init_storage();
void init_sensors();
void init_industrial_comms();
void init_gpio();

void app_main(void) {
  ESP_LOGI(TAG,
           "Iniciando Agente IA Agro-Inteligente - Nodo de Control ESP32-S3");

  // 1. Inicialización de Periféricos
  init_gpio();             // Configuración de Relés y Entradas
  init_storage();          // SD Card vía SPI
  init_sensors();          // DS18B20 OneWire
  init_industrial_comms(); // RS485 UART

  // 2. Loop de Ejecución del Agente
  while (1) {
    // TODO: Adquisición de datos (Sensores OneWire y Modbus)
    // TODO: Lógica de inferencia o control local (Agro-Inteligencia)
    // TODO: Persistencia en SD y reporte de telemetría
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void init_gpio() {
  ESP_LOGI(TAG, "Configurando GPIOs de Control (Relés)...");

  // Configuración de Relés como salida
  gpio_config_t io_conf = {
      .pin_bit_mask = (1ULL << RELAY_1_IO) | (1ULL << RELAY_2_IO),
      .mode = GPIO_MODE_OUTPUT,
      .pull_up_en = GPIO_PULLUP_DISABLE,
      .pull_down_en = GPIO_PULLDOWN_DISABLE,
      .intr_type = GPIO_INTR_DISABLE,
  };
  gpio_config(&io_conf);

  // Estado inicial seguro (Apagado)
  gpio_set_level(RELAY_1_IO, 0);
  gpio_set_level(RELAY_2_IO, 0);

  ESP_LOGI(TAG, "Relés inicializados en GPIO %d y %d", RELAY_1_IO, RELAY_2_IO);
}

void init_storage() {
  ESP_LOGI(TAG, "Configurando almacenamiento SD (CS: GPIO %d)", SD_CS_IO);
}

void init_sensors() {
  ESP_LOGI(TAG, "Buscando sensores en bus OneWire (GPIO %d)", ONEWIRE_BUS_IO);
}

void init_industrial_comms() {
  ESP_LOGI(TAG,
           "Puerto RS485 activo para comunicación industrial (TX:%d RX:%d)",
           RS485_TX_IO, RS485_RX_IO);
}