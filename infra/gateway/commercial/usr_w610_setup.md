# USR-W610 - Gateway Modbus RTU a WiFi/Ethernet

## Descripcion
El USR-W610 es un gateway serial-to-WiFi/Ethernet industrial.
Convierte Modbus RTU (RS-485) del PM8000 a Modbus TCP accesible por red.

## Conexion Fisica

```
PM8000 (RS-485 A/B) --> USR-W610 (RS-485 A/B) --> WiFi/Ethernet --> Red local
```

- PM8000 pin A (D1) --> W610 pin A
- PM8000 pin B (D0) --> W610 pin B
- GND comun recomendado

## Configuracion del USR-W610

### 1. Acceso al panel web
- Conectar al WiFi del W610 (AP: USR-W610_xxxx)
- Navegar a `http://10.10.100.254`
- Usuario: admin / Password: admin

### 2. Configuracion Serial (Serial Port Settings)
| Parametro | Valor |
|-----------|-------|
| Baud Rate | 19200 |
| Data Bits | 8 |
| Stop Bits | 1 |
| Parity | Even |
| Flow Control | None |

### 3. Configuracion de Red (Network Settings)
| Parametro | Valor |
|-----------|-------|
| Work Mode | TCP Server |
| Local Port | 502 |
| Protocol | Modbus TCP <-> RTU |
| Max Connections | 4 |

### 4. WiFi (si aplica)
- Mode: STA (Station)
- SSID: [su red WiFi]
- Password: [su password]
- Obtener IP por DHCP o configurar IP estatica

### 5. Ethernet (si aplica)
- Conectar cable RJ45
- DHCP o IP estatica segun su red

## Configuracion para Tailscale
El W610 NO soporta Tailscale directamente. Opciones:
1. **Subnet router**: Instalar Tailscale en otro dispositivo de la red (RPi, PC)
   y configurarlo como subnet router para exponer la IP del W610.
   ```bash
   tailscale up --advertise-routes=192.168.1.0/24
   ```
2. **Red local**: Si el servidor backend esta en la misma red, no necesita Tailscale.

## Verificacion
Desde el servidor backend:
```bash
# Instalar mbpoll para testing
pip install mbpoll
# o en Linux: apt install mbpoll

# Leer tension fase A (registro 2999, 2 registros float32)
mbpoll -a 1 -t 3:float -r 2999 -c 1 <IP_W610>

# Debe mostrar un valor de tension (~220V)
```

## Notas
- El W610 agrega ~5-10ms de latencia por request
- Soporta hasta 4 conexiones TCP simultaneas
- Si se pierde la conexion serial, reiniciar el W610
- Firmware actualizable via web panel
