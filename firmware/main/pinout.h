#ifndef PINOUT_H
#define PINOUT_H

// RS485 (UART2)
#define RS485_TX_IO 17
#define RS485_RX_IO 18
#define RS485_RTS_IO 19

// SD Card (SPI)
#define SD_SCK_IO 12
#define SD_MISO_IO 13
#define SD_MOSI_IO 11
#define SD_CS_IO 10

// Relays & Buttons
#define RELAY_1_IO 4
#define RELAY_2_IO 5
#define BTN_1_IO 6
#define BTN_2_IO 7

// Sensors & I2C
#define ONEWIRE_BUS_IO 21
#define I2C_SDA_IO 8
#define I2C_SCL_IO 9

#endif