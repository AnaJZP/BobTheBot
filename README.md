<p align="center">
  <img src="docs/assets/bob_avatar.png" alt="Bob the Bot" width="160">
</p>

# Bob the Bot - Bot de Telegram para Análisis Bursátil

Bob the Bot es un asistente de Telegram desarrollado en Python que ofrece análisis técnico básico de activos financieros. Interpreta consultas en lenguaje natural y comandos, y responde con una recomendación basada en los indicadores **Parabolic SAR** y **Oscilador Estocástico**, junto con un gráfico.

Pruébalo en Telegram: [@BobAnalisisBursatil_bot](https://t.me/BobAnalisisBursatil_bot)

El manual completo (creación con @BotFather, uso y funcionamiento interno) está en [Manual_Bob_the_Bot.pdf](Manual_Bob_the_Bot.pdf).

## Características principales

- **Lenguaje natural y comandos**: responde a `/analizar AAPL` y también a preguntas como "¿Qué opinas de Tesla?".
- **Análisis técnico automatizado**: calcula los indicadores con `pandas` y genera una señal de Compra, Venta o Mantener con su fuerza (fuerte, moderada o débil).
- **Gráfico de velas**: velas japonesas con Parabolic SAR y Oscilador Estocástico, enviadas junto con el análisis en un solo mensaje.
- **Ventanas de tiempo**: 1 hora, 4 horas y 1 día, con botones para cambiar entre ellas.
- **Menú por mercado y sector**: Mercado mexicano (BMV), SIC y ETFs, cada uno dividido en sectores (financiero, consumo, tecnología, índices, renta fija, etc.).
- **Detección de tickers**: reconoce `$AMZN`, nombres de empresas (Tesla, Coca-Cola, Bimbo, Walmex...), palabras en MAYÚSCULAS y mensajes de una sola palabra.
- **Mercado mexicano, índices y cripto**: `WALMEX.MX`, `^MXX`, `^GSPC`, `BTC-USD`, `MXN=X`.
- **Respuesta rápida**: el trabajo pesado corre en un hilo aparte y los datos se guardan en caché 5 minutos.
- **Registro de consultas**: guarda un historial en `consultas_bot.csv`.

## Instalación y puesta en marcha

### Requisitos

- Python 3.10 o superior.
- Una cuenta de Telegram.

### 1. Clonar el repositorio

```bash
git clone https://github.com/AnaJZP/BobTheBot.git
cd BobTheBot
```

### 2. Crear un entorno virtual

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear el bot en Telegram con @BotFather

1. Abre Telegram y busca la cuenta verificada `@BotFather`.
2. Envía el comando `/newbot`.
3. Elige un nombre público (ej. `Bob the Bot`) y un nombre de usuario único que termine en `bot` (ej. `MiBobElBot`).
4. BotFather te dará un token. **Cópialo y guárdalo en un lugar seguro**: quien lo tenga puede controlar el bot.

### 5. Configurar el token

El token **no se escribe en el código**. Crea un archivo `.env` en la carpeta del proyecto con esta línea:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
```

También puedes exportarlo como variable de entorno (`export TELEGRAM_BOT_TOKEN=...`). El archivo `.env` está en `.gitignore` y nunca se sube al repositorio.

Variable opcional: `BOB_CHART_BARS` (velas que se muestran en el gráfico, por defecto `120`).

### 6. Ejecutar el bot

```bash
python main.py
```

Si todo está correcto verás `Bot iniciado. Presiona Ctrl+C para detener.` en la terminal. El bot solo responde mientras el programa esté corriendo.

## Uso del bot

- `/start`: bienvenida con el botón **Explorar mercados** y ejemplos.
- `/mercados`: menú mercado (BMV, SIC, ETFs) → sector → activo.
- `/analizar AAPL`: análisis de un activo (hasta 3 a la vez: `/analizar AAPL MSFT KO`).
- `/analizar AAPL 4h`: análisis en otra ventana de tiempo (`1h`, `4h` o `1d`).
- `/ayuda`: lista de comandos y ejemplos.
- Mensajes libres: "¿Cómo ves a GOOG?", "¿Compro bimbo?", "$AMZN", "Tesla en 4 horas".

Cada respuesta incluye el gráfico de velas, la señal con su justificación, el detalle de cada indicador y botones para cambiar de ventana (**1 hora**, **4 horas**, **1 día**), **Actualizar** y volver a **Mercados**.

| Ventana | Historia usada | Nota |
|---|---|---|
| 1 hora | 60 días | Velas de 1 h de Yahoo Finance |
| 4 horas | 200 días | Se arman agrupando velas de 1 h dentro de cada sesión |
| 1 día (por defecto) | 1 año | Velas diarias |

Las emisoras del SIC se analizan con su ticker de origen en EE.UU., que tiene más historia e intradía que su réplica en la BMV.

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada. |
| `bot_logic.py` | Handlers de Telegram (comandos, texto libre, botones), formato de la respuesta y manejo de errores. |
| `config.py` | Lee el token y los parámetros desde variables de entorno o `.env`. |
| `ticker_parser.py` | Detecta el ticker y la ventana de tiempo en los mensajes. |
| `catalog.py` | Catálogo del menú: mercado → sector → activos. Para agregar un activo basta con añadirlo aquí. |
| `data_provider.py` | Velas y precio con `yfinance` según la ventana (1h, 4h, 1d), con caché de 5 minutos. |
| `technical_analysis.py` | Parabolic SAR, Oscilador Estocástico y señal combinada. |
| `charts.py` | Gráfico de velas con SAR y Estocástico en PNG. |
| `query_logger.py` | Registro de consultas en `consultas_bot.csv` (no se versiona: contiene IDs de usuarios). |
| `Manual_Bob_the_Bot.pdf` | Manual completo en tres partes: puesta en marcha, uso y funcionamiento interno. |
| `docs/generar_pdfs.py` | Regenera el manual. |
| `docs/generar_avatar.py` | Genera la imagen de perfil del bot (`docs/assets/bob_avatar.png`). |

Para regenerar el manual:

```bash
pip install reportlab
python docs/generar_pdfs.py
```

Para la foto de perfil del bot, envía `docs/assets/bob_avatar.png` a @BotFather con el comando `/setuserpic`.

## Descargo de responsabilidad

Este bot es una herramienta con fines educativos y de demostración. Sus análisis se basan únicamente en datos históricos e indicadores técnicos automatizados. **Esta información no constituye asesoramiento financiero.** Realiza siempre tu propia investigación y considera múltiples factores antes de tomar cualquier decisión de inversión.

## Contribuciones

Las contribuciones son bienvenidas. Si encuentras un error o tienes ideas para mejorar el bot, abre un issue o envía un pull request.

## Licencia

Este proyecto es de libre acceso.
