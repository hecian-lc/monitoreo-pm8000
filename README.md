# Monitoreo PM

Plataforma de monitoreo en la nube para medidores **Schneider Electric** de la serie PowerLogic y EasyLogic. Soporta multiples dispositivos simultaneos con adquisicion de datos en tiempo real via Modbus TCP, almacenamiento en InfluxDB, dashboard web interactivo, y generacion automatica de informes tecnicos DOCX/PDF.

## Medidores Soportados

| Modelo | Serie | Comunicacion | Registros |
|--------|-------|-------------|-----------|
| **PM8000** | PowerLogic PM8000 | Modbus TCP / RTU | Voltaje, corriente, potencia, FP, THD, armonicos, energia, demanda |
| **PM5340** | PowerLogic PM5000 | Modbus TCP / RTU | Voltaje, corriente, potencia, FP, THD, energia |
| **PM2220** | EasyLogic PM2000 | Modbus RTU | Voltaje, corriente, potencia, FP, THD, energia |

Todos los medidores se configuran desde la interfaz web. Se pueden agregar, modificar y eliminar dispositivos en cualquier momento. Cada uno tiene su propia conexion Modbus, mapa de registros y ciclo de polling independiente.

## Arquitectura

```
Medidores (RS-485/TCP)  -->  Gateways (RPi / ESP32 / Comercial)  -->  Tailscale VPN
                                                                           |
                                                                     Backend (FastAPI)
                                                                           |
                                                              InfluxDB + SQLite + WebSocket
                                                                           |
                                                                     Frontend (React)
```

| Componente | Tecnologia |
|------------|-----------|
| Backend | Python 3.11+ / FastAPI / pymodbus / influxdb-client |
| Frontend | React 18 / TypeScript / Vite / Tailwind / Recharts |
| Base de datos | InfluxDB 2.7 (series temporales) + SQLite (config) |
| Informes | python-docx + matplotlib (formato identico a circutor-report-generator) |
| Comunicacion | Modbus TCP, WebSocket, REST API |
| Acceso remoto | Tailscale VPN |

## Funcionalidades

- **Multi-dispositivo** - Agregar, modificar y eliminar multiples medidores (PM8000, PM5340, PM2220), cada uno con su propia conexion y polling
- **Dashboard en tiempo real** - Voltaje, corriente, potencia, FP, THD, frecuencia con actualizacion cada 1 segundo
- **Mediciones nombradas** - Crear sesiones de grabacion vinculadas a un dispositivo, iniciar/detener/comprimir/eliminar
- **Tendencias** - Graficas interactivas con zoom, selector de variables y rangos temporales
- **Tabla de datos** - Visualizacion tabular con filtros y exportacion CSV/XLSX
- **Informes automaticos** - DOCX/PDF con portada, tabla resumen 21x8, graficos, observaciones (reglas ANDE/IEEE 519 o Gemini AI)
- **Reportes programados** - Trigger manual o automatico por cron (fecha/hora)
- **Downsampling automatico** - 4 niveles de resolucion (1s, 1min, 15min, 1h) con retencion configurable
- **3 opciones de gateway** - Raspberry Pi, ESP32, o gateway comercial (USR-W610, Teltonika)
- **Test de conexion** - Verificar conectividad Modbus desde la interfaz web antes de iniciar mediciones

---

## Instalacion

### Requisitos previos

- **Docker** y **Docker Compose** (para InfluxDB)
- **Python 3.11+** (backend)
- **Node.js 18+** (frontend)
- Un gateway conectado al medidor (ver seccion Gateways)

### 1. Clonar el repositorio

```bash
git clone https://github.com/walc72/monitoreo-pm8000.git
cd monitoreo-pm8000
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar `.env`:

```env
# InfluxDB (dejar valores por defecto para desarrollo)
INFLUXDB_TOKEN=monitoreo-pm8000-token

# Gemini AI (opcional, para observaciones con IA en informes)
GEMINI_API_KEY=
```

> La configuracion de conexion Modbus ahora se hace por dispositivo desde la interfaz web (Dispositivos), no por variables de entorno.

### 3. Levantar InfluxDB

```bash
docker compose up -d influxdb
```

Verificar en http://localhost:8086 (usuario: admin / password: monitoreo2026)

### 4. Instalar y ejecutar el backend

```bash
cd backend
pip install .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API disponible en http://localhost:8000/docs (Swagger UI)

### 5. Instalar y ejecutar el frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard disponible en http://localhost:3000

### Alternativa: Todo con Docker Compose

```bash
docker compose up -d
```

Acceder a:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- InfluxDB UI: http://localhost:8086

---

## Manual de Uso

### 1. Agregar un Dispositivo

Antes de crear mediciones, debe agregar al menos un medidor:

1. Ir a **Dispositivos** en el menu lateral
2. Clic en **Agregar Dispositivo**
3. Completar:
   - **Nombre**: Ej: "PM8000 Tablero General"
   - **Modelo**: PM8000, PM5340 o PM2220
   - **IP / Host**: IP del gateway o del medidor (ej: 192.168.1.100)
   - **Puerto**: 502 (por defecto Modbus TCP)
   - **Unit ID**: 1 (por defecto)
   - **Intervalo**: 1.0 segundos
4. Clic en **Crear**
5. Usar el boton **Test** para verificar la conexion Modbus

> El sistema selecciona automaticamente el mapa de registros correcto segun el modelo. Cada dispositivo tiene su propio ciclo de polling independiente.

### 2. Gestionar Dispositivos

En la pagina **Dispositivos**:

- **Test**: Verifica la conexion Modbus al medidor. Muestra check verde si conecta o X roja si falla
- **Editar**: Modificar nombre, modelo, IP, puerto o intervalo. Al cambiar de modelo se actualiza automaticamente el mapa de registros
- **Eliminar**: Elimina el dispositivo y TODAS sus mediciones y datos asociados

Los badges de color indican el modelo:
- **PM8000** (indigo) - PowerLogic PM8000
- **PM5340** (teal) - PowerLogic PM5340
- **PM2220** (naranja) - EasyLogic PM2220

### 3. Crear una Medicion

Una **medicion** es una sesion de grabacion de datos vinculada a un dispositivo especifico.

1. Ir a **Mediciones** en el menu lateral
2. Clic en **Nueva Medicion**
3. Completar:
   - **Dispositivo**: Seleccionar el medidor a utilizar
   - **Nombre**: Ej: "TG Principal - Abril 2026"
   - **Descripcion**: Opcional
   - **Punto de medicion**: Ej: "T.G. - Corte General"
4. Clic en **Crear**

### 4. Iniciar la Grabacion

1. En la lista de mediciones, buscar la medicion creada
2. Clic en el boton **Play** (verde) para iniciar
3. El estado cambia a **Grabando** y el indicador rojo aparece en el header
4. Los datos del medidor se almacenan automaticamente cada 1 segundo

> Cada dispositivo puede tener una medicion grabando a la vez. Distintos dispositivos pueden grabar simultaneamente.

### 5. Ver Datos en Tiempo Real (Dashboard)

1. Ir a **Dashboard** en el menu lateral
2. Si hay multiples dispositivos, usar el selector en la esquina superior
3. Se muestran todos los parametros electricos en tiempo real:
   - **Tension de fase**: VAN, VBN, VCN (V)
   - **Tension de linea**: VAB, VBC, VCA (V)
   - **Corriente**: IA, IB, IC (A)
   - **Potencia activa/reactiva/aparente**: kW, kVAR, kVA
   - **Factor de potencia**: cos(phi) por fase y total
   - **THD**: Distorsion armonica de tension y corriente (%)
   - **Frecuencia**: Hz
4. El indicador de conexion en la esquina superior derecha muestra el estado

### 6. Ver Tendencias (Graficas)

1. Ir a **Tendencias** en el menu lateral
2. Seleccionar:
   - **Medicion**: elegir la medicion a consultar
   - **Categoria**: Tension, Corriente, Potencia, FP, THD, Frecuencia
   - **Rango temporal**: 1h, 6h, 24h, 7d, 30d
3. La grafica se actualiza automaticamente
4. Usar el **brush** (barra inferior) para hacer zoom en un rango especifico
5. El sistema auto-selecciona la resolucion optima:
   - < 1 hora: datos crudos (1 segundo)
   - < 24 horas: promedio cada 1 minuto
   - < 30 dias: promedio cada 15 minutos
   - Mas de 30 dias: promedio cada 1 hora

### 7. Tabla de Datos

1. Ir a **Datos** en el menu lateral
2. Seleccionar **Medicion**, **Fecha inicio** y **Fecha fin**
3. Clic en **Consultar**
4. La tabla muestra timestamp, variable, fase, categoria y valor
5. Para exportar:
   - Clic en **CSV** para descargar archivo separado por punto y coma
   - Clic en **Excel** para descargar archivo .xlsx

### 8. Detener una Medicion

1. Ir a **Mediciones**
2. Clic en el boton **Stop** (rojo) en la medicion activa
3. El estado cambia a **Detenida**
4. Los datos quedan almacenados y disponibles para consulta

### 9. Comprimir una Medicion

Cuando ya no necesita datos de alta resolucion (1 segundo), puede comprimir para ahorrar espacio:

1. Ir a **Mediciones**
2. Clic en el boton **Comprimir** (azul) en una medicion detenida
3. El sistema:
   - Conserva los datos downsampled (promedios de 1 minuto)
   - Elimina los datos crudos de 1 segundo
4. El estado cambia a **Comprimida** y la resolucion a "1min"

> La compresion es irreversible. Los datos de 1 segundo se eliminan permanentemente.

### 10. Eliminar una Medicion

1. Ir a **Mediciones**
2. Clic en el icono **Eliminar** (papelera)
3. Confirmar la eliminacion
4. Se eliminan TODOS los datos de esa medicion (InfluxDB + SQLite)

> La eliminacion es permanente e irreversible.

### 11. Generar un Informe

El informe se genera en formato DOCX (Word) o PDF, identico al formato del circutor-report-generator. Toda la configuracion y generacion se hace desde la pagina **Informes**:

1. Ir a **Informes** en el menu lateral
2. Completar el formulario superior:
   - **Medicion**: seleccionar la medicion a reportar
   - **Nombre**: nombre del informe
   - **Formato**: DOCX o PDF
   - **Observaciones**: Automatico (reglas), Gemini AI, o Manual
3. Clic en **Generar Informe**
4. Aparece un **modal de confirmacion** con:
   - Resumen de la medicion, formato y modo de observaciones
   - Campos editables: **Cliente**, **N Informe**, **Atencion** (pre-cargados de la configuracion guardada)
5. Clic en **Generar** para confirmar
6. El informe se genera en segundo plano (puede tardar 10-30 segundos)
7. Cuando el estado cambia a **completed**, clic en **Descargar**

#### Configuracion del Informe

En la misma pagina de **Informes**, abrir el panel colapsable **"Configuracion del Informe"** para editar:

- **Cliente**, **N Informe**, **Atencion**: Datos que aparecen en la caratula
- **Objetivo**, **Equipo**, **Periodicidad**: Textos tecnicos del informe
- **Nombre Firma**, **Cargo**: Datos de quien firma el informe
- **Colores**: Principal, fases R/S/T, trifasico (para graficos y tablas)

Estos valores se guardan y se pre-cargan en el modal cada vez que se genera un informe.

#### Contenido del informe:

| Pagina | Contenido |
|--------|-----------|
| 1 | Portada con logo y nombre del cliente |
| 2 | Datos del informe + tabla resumen 21x8 con todos los parametros |
| 3-5 | Graficos: tension fase/linea, corriente, potencia, FP, THD |
| 6 | Conclusion: observaciones y recomendaciones |

#### Modos de observaciones:

- **Automatico (Reglas)**: Compara datos contra normas ANDE/IEEE 519 y genera observaciones automaticas
  - Tension fase: 220V +/- 10% (norma ANDE)
  - Tension linea: 380V +/- 10% (norma ANDE)
  - Factor de potencia: >= 0.92 (Pliego N 21 ANDE)
  - THD tension: < 8% (IEEE 519)
  - Frecuencia: 50 Hz +/- 2%
- **Gemini AI**: Envia los datos a Gemini y genera observaciones con IA (requiere API key en Configuracion)
- **Manual**: El usuario escribe sus propias observaciones

#### Imagenes del Informe

Para agregar portada, encabezado y pie de pagina personalizados, copie las imagenes a:
```
backend/app/reports/assets/
  portada.png       (A4, 21x29.7cm)
  encabezado.png    (21x5.28cm)
  pie.png           (21x2.18cm)
```

### 12. Programar Informes Automaticos

Para generar informes de forma recurrente (ej: todos los lunes a las 8am):

1. Los reportes programados se configuran via la API:
   ```
   POST /api/reports/schedules
   {
     "name": "Reporte semanal TG",
     "measurement_id": "abc123",
     "cron_expression": "0 8 * * 1",
     "config": {"format": "docx", "observaciones_mode": "auto"}
   }
   ```
2. El sistema genera el informe automaticamente segun el cron

---

## Gateways

Los medidores hablan Modbus RTU (RS-485) o Modbus TCP (Ethernet). Se necesita un gateway para conectarlos a la red/WiFi/4G.

### Opcion 1: Raspberry Pi

La opcion mas flexible. La RPi ejecuta `mbusd` (bridge Modbus TCP-RTU) y Tailscale para acceso remoto.

```bash
cd infra/gateway/rpi
sudo ./setup.sh
sudo tailscale up
```

Ver `infra/gateway/rpi/setup.sh` para detalles.

### Opcion 2: ESP32

La opcion mas economica (~$5 USD). El ESP32 conecta al medidor por RS-485 y sirve Modbus TCP por WiFi.

```bash
cd infra/gateway/esp32
pio run --target upload
```

Configurar WiFi por serial: conectar y escribir `config`.

Ver `infra/gateway/esp32/src/main.cpp` para detalles.

### Opcion 3: Gateway Comercial

Para instalaciones industriales que requieren confiabilidad maxima:

- **USR-W610**: WiFi/Ethernet. Ver `infra/gateway/commercial/usr_w610_setup.md`
- **Teltonika RUT956**: 4G/LTE con Tailscale nativo. Ver `infra/gateway/commercial/teltonika_setup.md`

### Conexion directa por Ethernet

Si el medidor tiene puerto Ethernet (PM8000) y esta en la misma red que el servidor, no necesita gateway. Agregue el dispositivo con la IP del medidor directamente.

---

## Estructura del Proyecto

```
monitoreo-pm8000/
├── docker-compose.yml           # InfluxDB + backend + frontend
├── .env.example                 # Variables de entorno
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + lifespan
│   │   ├── config.py            # Configuracion via env vars
│   │   ├── collector/           # CollectorManager + polling multi-device
│   │   ├── db/                  # InfluxDB + SQLite
│   │   ├── api/endpoints/       # REST + WebSocket endpoints
│   │   ├── reports/             # DOCX/PDF generation
│   │   ├── scheduler/           # APScheduler (reportes automaticos)
│   │   └── models/              # Pydantic models
│   └── registers/
│       ├── pm8000_default.yaml  # Mapa registros PM8000
│       ├── pm5340_default.yaml  # Mapa registros PM5340
│       └── pm2220_default.yaml  # Mapa registros PM2220
├── frontend/
│   └── src/
│       ├── pages/               # Dashboard, Trends, Data, Devices, Measurements, Reports (con config), Settings
│       ├── components/          # Layout, Dashboard, Charts
│       ├── api/                 # REST client + WebSocket manager
│       ├── hooks/               # useRealtimeData, useHistoricalData
│       └── store/               # Zustand stores
└── infra/gateway/               # RPi, ESP32, commercial gateway configs
```

## API

Documentacion interactiva disponible en http://localhost:8000/docs (Swagger UI)

### Endpoints principales

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/health` | Estado del sistema y todos los dispositivos |
| GET | `/api/devices/models` | Listar modelos de medidores soportados |
| GET/POST | `/api/devices` | Listar/crear dispositivos |
| PUT | `/api/devices/{id}` | Modificar dispositivo |
| DELETE | `/api/devices/{id}` | Eliminar dispositivo y sus datos |
| POST | `/api/devices/{id}/test` | Probar conexion Modbus |
| GET/POST | `/api/measurements` | Listar/crear mediciones |
| POST | `/api/measurements/{id}/action` | Iniciar/detener/comprimir |
| DELETE | `/api/measurements/{id}` | Eliminar medicion y datos |
| GET | `/api/data/query` | Consultar datos historicos |
| GET | `/api/data/stats` | Estadisticas min/max/mean |
| GET | `/api/export/csv` | Exportar datos como CSV |
| GET | `/api/export/xlsx` | Exportar datos como Excel |
| POST | `/api/reports/generate` | Generar informe DOCX/PDF |
| GET | `/api/reports/{id}/download` | Descargar informe |
| GET/PUT | `/api/reports/config` | Config de informes |
| WS | `/ws/realtime` | WebSocket datos en tiempo real |

## Licencia

MIT
