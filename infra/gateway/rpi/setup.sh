#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Raspberry Pi Gateway Setup Script
# Configura mbusd (Modbus TCP-to-RTU gateway) + Tailscale
#
# Conexion fisica:
#   PM8000 (RS-485) --> Adaptador USB-RS485 --> RPi (ttyUSB0)
#   RPi (WiFi/ETH) --> Tailscale VPN --> Servidor Backend
#
# Uso:
#   chmod +x setup.sh
#   sudo ./setup.sh
# ─────────────────────────────────────────────────────────────
set -e

echo "=== Gateway RPi para PM8000 ==="
echo ""

# ── 1. Actualizar sistema ──
echo "[1/5] Actualizando sistema..."
apt-get update -qq
apt-get upgrade -y -qq

# ── 2. Instalar mbusd (Modbus TCP to RTU gateway) ──
echo "[2/5] Instalando mbusd..."
apt-get install -y -qq git build-essential cmake

if [ ! -d "/opt/mbusd" ]; then
    git clone https://github.com/3cky/mbusd.git /opt/mbusd
fi

cd /opt/mbusd
mkdir -p build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/usr ..
make -j$(nproc)
make install

# ── 3. Configurar mbusd ──
echo "[3/5] Configurando mbusd..."
SERIAL_PORT="${SERIAL_PORT:-/dev/ttyUSB0}"
BAUD_RATE="${BAUD_RATE:-19200}"
PARITY="${PARITY:-even}"
TCP_PORT="${TCP_PORT:-502}"

cat > /etc/mbusd.conf <<EOF
# mbusd configuration for PM8000
# Serial port (RS-485 adapter)
device = ${SERIAL_PORT}
speed = ${BAUD_RATE}
parity = ${PARITY}
stopbits = 1

# TCP server
bind = 0.0.0.0
port = ${TCP_PORT}
maxconn = 4
timeout = 3

# Logging
loglevel = 2
logfile = /var/log/mbusd.log
EOF

# Crear servicio systemd
cat > /etc/systemd/system/mbusd.service <<EOF
[Unit]
Description=Modbus TCP to RTU Gateway (mbusd)
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/mbusd -d -c /etc/mbusd.conf
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable mbusd
systemctl start mbusd

echo "  mbusd configurado: ${SERIAL_PORT} @ ${BAUD_RATE} baud -> TCP :${TCP_PORT}"

# ── 4. Instalar Tailscale ──
echo "[4/5] Instalando Tailscale..."
if ! command -v tailscale &> /dev/null; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

echo ""
echo "  Para conectar a su red Tailscale, ejecute:"
echo "    sudo tailscale up"
echo ""
echo "  Luego obtenga la IP de Tailscale con:"
echo "    tailscale ip -4"

# ── 5. Reglas de firewall (permitir Modbus TCP) ──
echo "[5/5] Configurando firewall..."
if command -v ufw &> /dev/null; then
    ufw allow ${TCP_PORT}/tcp comment "Modbus TCP (mbusd)"
    echo "  Puerto ${TCP_PORT}/tcp abierto en UFW"
fi

echo ""
echo "=== Instalacion completada ==="
echo ""
echo "Resumen:"
echo "  - mbusd: ${SERIAL_PORT} @ ${BAUD_RATE} -> TCP :${TCP_PORT}"
echo "  - Servicio: systemctl status mbusd"
echo "  - Log: /var/log/mbusd.log"
echo ""
echo "Proximos pasos:"
echo "  1. Conecte el adaptador USB-RS485 al PM8000"
echo "  2. Ejecute: sudo tailscale up"
echo "  3. En el servidor backend, configure MODBUS_HOST con la IP Tailscale de esta RPi"
echo "  4. Verifique con: mbpoll -a 1 -t 3 -r 2999 -c 2 <IP_TAILSCALE>"
echo ""
echo "Parametros del PM8000 (verificar en el medidor):"
echo "  - Baud rate: ${BAUD_RATE}"
echo "  - Paridad: ${PARITY}"
echo "  - Unit ID: 1"
echo "  - Protocolo: Modbus RTU"
