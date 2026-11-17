# Bob the Bot – Bot de Telegram para Análisis Bursátil

Bot de Telegram en Python que entrega un análisis técnico básico de acciones, índices y
criptoactivos usando **Parabolic SAR** y **Oscilador Estocástico (14,3,3)**, con una gráfica
del activo. Proyecto educativo del curso *Análisis Bursátil y Métodos Algorítmicos Avanzados*
(SEPI ESE IPN).

Bot del curso en Telegram: [@BobAnalisisBursatil_bot](https://t.me/BobAnalisisBursatil_bot)

## Características

- Comandos (`/analizar AAPL`) y lenguaje natural («¿Qué opinas de Tesla?», «¿Cómo ves a Walmex?»).
- Emisoras de la BMV con sufijo `.MX` (`GFNORTEO.MX`, `AMXB.MX`) e índices (`^MXX`).
- Indicadores implementados en `pandas`/`numpy` (sin dependencias difíciles de instalar).
- Gráfica de precio + SAR + Estocástico enviada como imagen.
- Registro de consultas en `logs/consultas_bot.csv` (fuera del repositorio).
- Pruebas unitarias con `pytest`.

## Requisitos

- Python **3.10 o superior**
- Git
- Una cuenta de Telegram

## Instalación

```bash
git clone https://github.com/AnaJZP/BobTheBot.git
cd BobTheBot
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Crear el bot en Telegram (@BotFather)

1. En Telegram busca **@BotFather** (cuenta verificada) y envía `/newbot`.
2. Escribe el **nombre visible** (ej. `Bob the Bot`) y un **usuario** único que termine en `bot`
   (ej. `BobAnalistaIPN_bot`).
3. BotFather responde con el **token** (`123456789:AA...`). Ábrelo en tu `.env`:

   ```
   TELEGRAM_BOT_TOKEN=123456789:AA...
   ```

4. Opcional: `/setdescription`, `/setabouttext` y `/setuserpic` para personalizar el bot.
   El menú de comandos se configura solo al iniciar el bot.

> **Seguridad:** el token da control total del bot. Nunca lo escribas en un archivo `.py`
> ni lo subas a GitHub. Si se filtra, en @BotFather usa `/revoke` para generar uno nuevo.

## Ejecutar

```bash
python main.py
```

Verás `Bot iniciado. Presiona Ctrl+C para detener.` Abre tu bot en Telegram, pulsa **Iniciar**
y prueba `/analizar AAPL`. El bot funciona mientras la terminal esté abierta.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Estructura

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. |
| `config.py` | Lee el token y los parámetros desde `.env`. |
| `bot_logic.py` | Capa de Telegram: comandos, mensajes y respuestas. |
| `ticker_parser.py` | Identifica el ticker en el texto del usuario. |
| `data_provider.py` | Descarga precios con `yfinance` (único módulo que conoce la fuente de datos). |
| `indicators.py` | Fórmulas del Parabolic SAR y del Estocástico. |
| `technical_analysis.py` | Reglas de señal y recomendación consolidada. |
| `charts.py` | Gráfica en memoria con `matplotlib`. |
| `query_logger.py` | Registro CSV de consultas. |
| `tests/` | Pruebas unitarias. |

Flujo de una consulta:

```
Usuario → Telegram → bot_logic ─┬→ ticker_parser        (¿qué activo?)
                                ├→ data_provider        (precios)
                                ├→ technical_analysis → indicators  (señal)
                                ├→ charts               (gráfica)
                                └→ query_logger         (registro)
Usuario ← Telegram ← bot_logic  (texto + gráfica)
```

## Descargo de responsabilidad

Herramienta educativa. Las señales se basan solo en indicadores técnicos sobre datos
históricos y **no constituyen asesoramiento financiero**.
