/**
 * ESP32 Modbus TCP-to-RTU Bridge for PM8000
 *
 * Receives Modbus TCP requests from the backend server via WiFi
 * and forwards them as Modbus RTU to the PM8000 via RS-485.
 *
 * Wiring:
 *   ESP32 GPIO16 (RX) <-- RS-485 module RO
 *   ESP32 GPIO17 (TX) --> RS-485 module DI
 *   ESP32 GPIO4  (DE) --> RS-485 module DE + RE
 *   RS-485 A/B        <-> PM8000 RS-485 A/B
 *
 * Configuration:
 *   - WiFi credentials via build_flags or serial config
 *   - PM8000 defaults: 19200 baud, 8E1
 */

#include <Arduino.h>
#include <WiFi.h>
#include <ModbusIP_ESP8266.h>
#include <Preferences.h>

// ─── Pin definitions ───
#ifndef RS485_RX
#define RS485_RX 16
#endif
#ifndef RS485_TX
#define RS485_TX 17
#endif
#ifndef RS485_DE
#define RS485_DE 4  // Driver Enable (HIGH=transmit, LOW=receive)
#endif
#ifndef RS485_BAUD
#define RS485_BAUD 19200
#endif
#ifndef MODBUS_TCP_PORT
#define MODBUS_TCP_PORT 502
#endif

// ─── Globals ───
ModbusIP mb;
HardwareSerial RS485Serial(2);  // UART2
Preferences prefs;

String wifi_ssid;
String wifi_password;
bool configured = false;

// ─── RS-485 direction control ───
void rs485_transmit() { digitalWrite(RS485_DE, HIGH); }
void rs485_receive()  { digitalWrite(RS485_DE, LOW); }

// ─── Send Modbus RTU request and get response ───
// This is a simplified bridge - for each TCP request,
// we forward the raw RTU frame to the PM8000 and return the response.

uint16_t crc16(uint8_t *buf, int len) {
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < len; i++) {
        crc ^= buf[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1) crc = (crc >> 1) ^ 0xA001;
            else crc >>= 1;
        }
    }
    return crc;
}

bool modbus_rtu_request(uint8_t unit_id, uint8_t func_code,
                         uint16_t start_addr, uint16_t quantity,
                         uint16_t *response, int *resp_count) {
    uint8_t request[8];
    request[0] = unit_id;
    request[1] = func_code;
    request[2] = (start_addr >> 8) & 0xFF;
    request[3] = start_addr & 0xFF;
    request[4] = (quantity >> 8) & 0xFF;
    request[5] = quantity & 0xFF;
    uint16_t crc = crc16(request, 6);
    request[6] = crc & 0xFF;
    request[7] = (crc >> 8) & 0xFF;

    // Clear RX buffer
    while (RS485Serial.available()) RS485Serial.read();

    // Send request
    rs485_transmit();
    RS485Serial.write(request, 8);
    RS485Serial.flush();
    rs485_receive();

    // Wait for response (timeout 1000ms)
    unsigned long start = millis();
    int expected_bytes = 3 + quantity * 2 + 2;  // header + data + CRC
    uint8_t resp_buf[256];
    int idx = 0;

    while ((millis() - start) < 1000 && idx < expected_bytes) {
        if (RS485Serial.available()) {
            resp_buf[idx++] = RS485Serial.read();
            start = millis();  // Reset timeout on each byte
        }
    }

    if (idx < 5) return false;  // Too short

    // Verify CRC
    uint16_t resp_crc = crc16(resp_buf, idx - 2);
    uint16_t recv_crc = resp_buf[idx - 2] | (resp_buf[idx - 1] << 8);
    if (resp_crc != recv_crc) return false;

    // Check for error response
    if (resp_buf[1] & 0x80) return false;

    // Parse response data
    int byte_count = resp_buf[2];
    *resp_count = byte_count / 2;
    for (int i = 0; i < *resp_count && i < (int)quantity; i++) {
        response[i] = (resp_buf[3 + i * 2] << 8) | resp_buf[4 + i * 2];
    }

    return true;
}

// ─── Modbus TCP callback ───
// The ModbusIP library handles TCP connections.
// We use a polling approach: periodically read PM8000 registers
// and serve them from the ESP32's internal register map.

// Register ranges to poll from PM8000
struct RegBlock {
    uint16_t start;
    uint16_t count;
};

RegBlock blocks[] = {
    {2999, 46},   // Voltages + currents
    {3053, 70},   // Power, PF, frequency
    {2699, 24},   // Energy
};
const int NUM_BLOCKS = 3;

unsigned long lastPoll = 0;
const unsigned long POLL_INTERVAL = 1000;  // 1 second

void pollPM8000() {
    for (int b = 0; b < NUM_BLOCKS; b++) {
        uint16_t response[125];
        int count = 0;

        if (modbus_rtu_request(1, 3, blocks[b].start, blocks[b].count,
                                response, &count)) {
            // Store in local Modbus TCP register map
            for (int i = 0; i < count; i++) {
                mb.Hreg(blocks[b].start + i, response[i]);
            }
        }
    }
}

// ─── WiFi Configuration ───
void loadConfig() {
    prefs.begin("modbus-gw", true);
    wifi_ssid = prefs.getString("ssid", WIFI_SSID);
    wifi_password = prefs.getString("pass", WIFI_PASSWORD);
    prefs.end();
    configured = wifi_ssid.length() > 0;
}

void saveConfig(const String &ssid, const String &pass) {
    prefs.begin("modbus-gw", false);
    prefs.putString("ssid", ssid);
    prefs.putString("pass", pass);
    prefs.end();
}

void serialConfig() {
    Serial.println("\n=== ESP32 Modbus Gateway Configuration ===");
    Serial.println("Enter WiFi SSID:");
    while (!Serial.available()) delay(100);
    String ssid = Serial.readStringUntil('\n');
    ssid.trim();

    Serial.println("Enter WiFi Password:");
    while (!Serial.available()) delay(100);
    String pass = Serial.readStringUntil('\n');
    pass.trim();

    saveConfig(ssid, pass);
    Serial.println("Config saved. Restarting...");
    delay(1000);
    ESP.restart();
}

// ─── Setup ───
void setup() {
    Serial.begin(115200);
    Serial.println("\nESP32 Modbus TCP-to-RTU Bridge");
    Serial.println("PM8000 Gateway v1.0");

    // RS-485 setup
    pinMode(RS485_DE, OUTPUT);
    rs485_receive();
    RS485Serial.begin(RS485_BAUD, SERIAL_8E1, RS485_RX, RS485_TX);

    // Load WiFi config
    loadConfig();
    if (!configured) {
        Serial.println("No WiFi configured. Enter config via serial...");
        serialConfig();
        return;
    }

    // Connect WiFi
    Serial.printf("Connecting to WiFi: %s\n", wifi_ssid.c_str());
    WiFi.begin(wifi_ssid.c_str(), wifi_password.c_str());

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(1000);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\nFailed to connect. Check config.");
        serialConfig();
        return;
    }

    // Setup Modbus TCP server
    mb.server(MODBUS_TCP_PORT);

    // Pre-allocate holding registers for all PM8000 register ranges
    for (int b = 0; b < NUM_BLOCKS; b++) {
        for (uint16_t i = 0; i < blocks[b].count; i++) {
            mb.addHreg(blocks[b].start + i, 0);
        }
    }

    Serial.printf("Modbus TCP server on port %d\n", MODBUS_TCP_PORT);
    Serial.printf("RS-485: %d baud, 8E1, DE=GPIO%d\n", RS485_BAUD, RS485_DE);
    Serial.println("Ready.");
}

// ─── Loop ───
void loop() {
    mb.task();  // Handle Modbus TCP connections

    // Poll PM8000 periodically
    if (millis() - lastPoll >= POLL_INTERVAL) {
        lastPoll = millis();
        pollPM8000();
    }

    // Check for serial config command
    if (Serial.available()) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd == "config") {
            serialConfig();
        } else if (cmd == "status") {
            Serial.printf("WiFi: %s (%s)\n",
                WiFi.status() == WL_CONNECTED ? "connected" : "disconnected",
                WiFi.localIP().toString().c_str());
            Serial.printf("Modbus TCP port: %d\n", MODBUS_TCP_PORT);
            Serial.printf("Free heap: %d bytes\n", ESP.getFreeHeap());
        }
    }

    // Reconnect WiFi if disconnected
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi lost, reconnecting...");
        WiFi.reconnect();
        delay(5000);
    }
}
