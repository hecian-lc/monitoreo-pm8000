# Teltonika TRB142 / RUT956 - Gateway Modbus 4G/LTE

## Descripcion
Los gateways Teltonika son ideales para sitios sin WiFi ni Ethernet.
Usan una SIM 4G/LTE para conectar el PM8000 a internet.

- **TRB142**: Gateway serial 4G compacto (RS-232, necesita adaptador a RS-485)
- **RUT956**: Router industrial 4G con RS-232/RS-485 integrado (recomendado)

## Conexion Fisica

```
PM8000 (RS-485) --> Teltonika RUT956 (RS-485) --> 4G/LTE --> Internet --> Tailscale --> Backend
```

### RUT956 (RS-485 directo)
- PM8000 A --> RUT956 terminal A
- PM8000 B --> RUT956 terminal B

### TRB142 (necesita conversor RS-232 a RS-485)
- PM8000 A/B --> Conversor RS-485/RS-232 --> TRB142 RS-232

## Configuracion del Teltonika

### 1. Acceso al panel web
- Conectar por Ethernet al puerto LAN
- Navegar a `http://192.168.1.1`
- Usuario: admin / Password: (en la etiqueta del dispositivo)

### 2. SIM y conexion 4G
- Insertar SIM con plan de datos
- Services > Mobile > SIM1: Configurar APN del operador
- Verificar conexion a internet

### 3. Modbus Gateway (Services > Modbus > Modbus TCP Gateway)
| Parametro | Valor |
|-----------|-------|
| Enable | On |
| Listening Port | 502 |
| Serial Type | RS-485 |
| Baud Rate | 19200 |
| Data Bits | 8 |
| Parity | Even |
| Stop Bits | 1 |
| Mode | Modbus TCP to RTU Gateway |

### 4. Tailscale (Services > VPN > Tailscale)
Los Teltonika modernos (RutOS 7.x+) soportan Tailscale nativo:
1. Ir a Services > VPN > Tailscale
2. Enable: On
3. Auth Key: generar en https://login.tailscale.com/admin/settings/keys
4. Pegar auth key y guardar
5. El dispositivo aparecera en su red Tailscale

Si no tiene Tailscale nativo, usar WireGuard o OpenVPN.

### 5. Firewall
- Network > Firewall > Traffic Rules
- Agregar regla: Allow TCP 502 from Tailscale interface

## Configuracion en el Backend
```bash
# .env
MODBUS_HOST=100.x.x.x  # IP Tailscale del Teltonika
MODBUS_PORT=502
MODBUS_UNIT_ID=1
```

## Verificacion
```bash
# Desde el servidor (con Tailscale conectado)
mbpoll -a 1 -t 3:float -r 2999 -c 1 100.x.x.x

# Debe mostrar tension de fase (~220V)
```

## Consumo de Datos 4G
Con polling cada 1 segundo (~100 registros por ciclo):
- ~500 bytes por request/response
- ~500 bytes/s = ~43 MB/dia = ~1.3 GB/mes
- Recomendacion: plan de datos de al menos 2 GB/mes

## Notas
- Latencia 4G tipica: 30-80ms (suficiente para polling 1s)
- El RUT956 tiene watchdog integrado para reinicio automatico
- Soporta SMS de alerta si pierde conexion
- Temperatura operativa: -40 a +75 C (uso industrial)
