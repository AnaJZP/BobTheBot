# Bob the Bot - Bot de Telegram para Análisis Bursátil

Bob the Bot es un asistente de Telegram desarrollado en Python que ofrece análisis técnicos básicos de activos financieros. El bot está diseñado para interpretar consultas en lenguaje natural y comandos específicos, entregando recomendaciones basadas en los indicadores **Parabolic SAR** y **Oscilador Estocástico**, junto con una visualización gráfica.

## 🌟 Características Principales

- **Interfaz de Usuario Dual**: Responde tanto a comandos directos (ej. `/analizar AAPL`) como a preguntas en lenguaje conversacional (ej. "¿Qué opinas de TSLA?").

- **Análisis Técnico Automatizado**: Calcula los indicadores con `pandas` y genera señales de "Compra", "Venta" o "Mantener" con su fuerza (fuerte, moderada o débil).

- **Visualización de Datos**: Genera y envía un gráfico creado con `matplotlib` que muestra el precio del activo, el Parabolic SAR y el Oscilador Estocástico para un análisis visual inmediato.

- **Extracción de Tickers**: Intenta identificar símbolos de activos (tickers) en los mensajes de los usuarios mediante expresiones regulares.

- **Registro de Consultas**: Almacena un historial de las consultas y las respuestas generadas en un archivo `consultas_bot.csv` para seguimiento y análisis de uso.

## 🔧 Instalación y Puesta en Marcha

Sigue estos pasos para configurar y ejecutar tu propia instancia de Bob the Bot.

### Prerrequisitos

- Python 3.10 o superior.
- Una cuenta de Telegram.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/AnaJZP/BobTheBot.git
cd BobTheBot
```

### 2. Crear un Entorno Virtual (Recomendado)

Para mantener las dependencias del proyecto aisladas:

```bash
# Para Windows
python -m venv venv
.\venv\Scripts\activate

# Para macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

El proyecto incluye un archivo `requirements.txt` con todas las librerías necesarias.

```bash
pip install -r requirements.txt
```

### 4. Crear el Bot en Telegram con BotFather

Para que el bot funcione, necesitas un TOKEN de acceso de la API de Telegram.

1. Abre Telegram y busca la cuenta verificada: `@BotFather`.
2. Inicia una conversación y envía el comando `/newbot`.
3. Sigue las instrucciones para elegir un nombre público (ej. `Bob the Bot`) y un nombre de usuario único que termine en `bot` (ej. `MiBobElBot`).
4. Al finalizar, BotFather te proporcionará un token. **Copia este token y guárdalo en un lugar seguro**.

### 5. Configurar el Token en el Proyecto

El token **no se escribe en el código**. Crea un archivo `.env` en la carpeta del proyecto con esta línea:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
```

También puedes exportarlo como variable de entorno (`export TELEGRAM_BOT_TOKEN=...`). El archivo `.env` está en `.gitignore`.

### 6. Ejecutar el Bot

Una vez instalado y configurado, inicia el bot con el siguiente comando, que ejecuta el archivo `main.py`:

```bash
python main.py
```

Si todo está correcto, verás el mensaje `Bot iniciado. Presiona Ctrl+C para detener.` en tu terminal. ¡Tu bot ya está en línea!

## 📁 Estructura del Proyecto

- **`main.py`**: Punto de entrada.
- **`bot_logic.py`**: Handlers de Telegram (comandos, texto libre, botones), formato de la respuesta y manejo de errores. El trabajo pesado corre en un hilo con `asyncio.to_thread` para no bloquear al bot.
- **`config.py`**: Lee el token y parámetros desde variables de entorno / `.env`.
- **`ticker_parser.py`**: Detecta el ticker en mensajes (`$AMZN`, nombres como "Tesla" o "Bimbo", palabras en MAYÚSCULAS).
- **`data_provider.py`**: Histórico y precio con `yfinance` en una sola petición, con caché de 5 minutos.
- **`technical_analysis.py`**: Parabolic SAR y Oscilador Estocástico (pandas puro) y la señal combinada con su fuerza.
- **`charts.py`**: Gráfico de precio + SAR + Estocástico en PNG.
- **`query_logger.py`**: Registro de consultas en `consultas_bot.csv` (no se versiona: contiene IDs de usuarios).
- **`Manual_Bob_the_Bot.pdf`**: Manual completo en tres partes: I. puesta en marcha desde @BotFather, II. uso del bot y III. funcionamiento interno.
- **`docs/generar_pdfs.py`**: Regenera el manual (sin conexión reutiliza el ejemplo guardado en `docs/assets/`):

  ```bash
  pip install reportlab
  python docs/generar_pdfs.py --bot-username @BobAnalisisBursatil_bot
  ```

## ⚖️ Descargo de Responsabilidad

Este bot es una herramienta creada con fines educativos y de demostración. Los análisis que proporciona se basan únicamente en datos históricos e indicadores técnicos automatizados. **Esta información no constituye asesoramiento financiero**. Siempre debes realizar tu propia investigación y considerar múltiples factores antes de tomar cualquier decisión de inversión.

## 📋 Uso del Bot

Una vez que el bot esté funcionando, puedes interactuar con él de varias maneras:

- Envía comandos directos como `/analizar AAPL` (hasta 3 tickers: `/analizar AAPL MSFT KO`)
- Haz preguntas en lenguaje natural como "¿Qué opinas de Tesla?" o "¿Compro bimbo?"
- Acciones mexicanas con `.MX` (`WALMEX.MX`), índices (`^GSPC`, `^MXX`), cripto (`BTC-USD`)
- Recibirás el gráfico con el análisis en un solo mensaje y un botón **🔄 Actualizar**

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes ideas para mejorar el bot, no dudes en abrir un issue o enviar un pull request.

## 📝 Licencia

Este proyecto es de libre acceso
