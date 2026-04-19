#include "esp_camera.h"
#include <Arduino.h>

/**
 * Configuración optimizada para ESP32-S3 (Freenove / AI-Thinker S3 / Generic S3
 * Cam)
 */

// Definición de pines para ESP32-S3
#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 15
#define SIOD_GPIO_NUM 4
#define SIOC_GPIO_NUM 5

#define Y9_GPIO_NUM 16
#define Y8_GPIO_NUM 17
#define Y7_GPIO_NUM 18
#define Y6_GPIO_NUM 12
#define Y5_GPIO_NUM 10
#define Y4_GPIO_NUM 8
#define Y3_GPIO_NUM 9
#define Y2_GPIO_NUM 11
#define VSYNC_GPIO_NUM 6
#define HREF_GPIO_NUM 7
#define PCLK_GPIO_NUM 13

bool setupCameraS3() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA; // Resolución máxima (1600x1200)
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM; // Obligatorio para S3 en UXGA
  config.jpeg_quality = 10;
  config.fb_count = 2; // Doble buffer para streaming fluido

  // Detección automática de PSRAM
  if (!psramFound()) {
    Serial.println("FATAL: PSRAM no encontrada. La ESP32-S3 requiere PSRAM "
                   "para modo Cámara.");
    return false;
  }

  // Inicializar la cámara
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error al iniciar cámara: 0x%x\n", err);
    return false;
  }

  // Ajustes del sensor para agricultura (mejorar contraste y saturación para
  // plantas)
  sensor_t *s = esp_camera_sensor_get();
  s->set_brightness(s, 0); // -2 a 2
  s->set_contrast(s, 1);   // -2 a 2 (Subido para resaltar texturas de hojas)
  s->set_saturation(
      s, 1); // -2 a 2 (Subido para detectar mejor clorosis/tonos verdes)
  s->set_whitebal(s, 1); // Auto White Balance

  Serial.println("Cámara ESP32-S3 configurada exitosamente.");
  return true;
}