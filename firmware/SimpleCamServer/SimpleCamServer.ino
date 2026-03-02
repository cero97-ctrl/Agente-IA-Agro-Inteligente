#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ==========================================
// CONFIGURACIÓN DE WIFI
// ==========================================
#include "wifi_credentials.h"
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;

// Seleccionar modelo de cámara
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// Pin del Flash (LED de alta potencia)
#define FLASH_GPIO_NUM 4

// Iniciar servidor en puerto 80
WebServer server(80);

void handleCapture() {
  // Capturar un frame
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Fallo en la captura de la cámara");
    server.send(500, "text/plain", "Error al capturar imagen");
    return;
  }

  // Enviar cabeceras y la imagen JPEG
  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.sendHeader("Access-Control-Allow-Origin", "*"); // CORS para pruebas web
  
  // Enviar el buffer de la imagen
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  
  // Liberar memoria
  esp_camera_fb_return(fb);
  Serial.println("Foto enviada correctamente");
}

void handleFlash() {
  if (server.hasArg("state")) {
    int state = server.arg("state").toInt();
    digitalWrite(FLASH_GPIO_NUM, state); // 1 = ON, 0 = OFF
    server.send(200, "text/plain", state ? "Flash ENCENDIDO" : "Flash APAGADO");
  } else {
    server.send(400, "text/plain", "Falta parametro 'state'");
  }
}

void handleRestart() {
  Serial.println("Solicitud de reinicio recibida.");
  server.send(200, "text/plain", "Reiniciando camara...");
  delay(1000); // Dar tiempo a que se envíe la respuesta
  ESP.restart();
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Configurar Flash
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW); // Asegurar que arranque apagado

  // Configuración de la cámara
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
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Ajustar calidad según si tiene PSRAM (memoria extra)
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA; // 1600x1200
    config.jpeg_quality = 10; // 0-63, menor es mejor calidad
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Inicializar cámara
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error iniciando cámara: 0x%x", err);
    return;
  }

  // Ajustes del sensor para mejorar la imagen (evitar fotos oscuras)
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 1);     // Aumentar brillo (-2 a 2)
    s->set_contrast(s, 1);       // Aumentar contraste (-2 a 2)
    s->set_saturation(s, 0);     // Saturación (-2 a 2)
    s->set_gain_ctrl(s, 1);      // Activar control de ganancia automático
    s->set_exposure_ctrl(s, 1);  // Activar control de exposición automático
    s->set_aec2(s, 1);           // Activar algoritmo AEC mejorado
    s->set_gainceiling(s, (gainceiling_t)6); // Permitir máxima ganancia en poca luz (0-6)
  }

  // "Calentar" la cámara: Tomar y descartar algunos frames para que el sensor se estabilice
  for (int i = 0; i < 4; i++) {
    camera_fb_t * fb = esp_camera_fb_get();
    esp_camera_fb_return(fb);
    delay(150);
  }

  // Configurar IP Estática (Para evitar que cambie cada vez)
  // Asegúrate de que la IP .25 esté libre en tu red
  IPAddress local_IP(192, 168, 0, 25); 
  IPAddress gateway(192, 168, 0, 1);   // Tu Router (según tu nmap anterior)
  IPAddress subnet(255, 255, 255, 0);
  WiFi.config(local_IP, gateway, subnet);

  // Conectar a WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.print("\nWiFi conectado. IP: http://");
  Serial.println(WiFi.localIP());

  // Rutas del servidor
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/restart", HTTP_GET, handleRestart);
  server.on("/flash", HTTP_GET, handleFlash);
  server.begin();
}

void loop() {
  server.handleClient();
}
