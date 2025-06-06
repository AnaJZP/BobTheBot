# Bob the Bot - Bot de Telegram para Análisis Bursátil

Bob the Bot es un asistente de Telegram desarrollado en Python que ofrece análisis técnicos básicos de activos financieros. El bot está diseñado para interpretar consultas en lenguaje natural y comandos específicos, entregando recomendaciones basadas en los indicadores **Parabolic SAR** y **Oscilador Estocástico**, junto con una visualización gráfica.

## 🌟 Características Principales

- **Interfaz de Usuario Dual**: Responde tanto a comandos directos (ej. `/analizar AAPL`) como a preguntas en lenguaje conversacional (ej. "¿Qué opinas de TSLA?").

- **Análisis Técnico Automatizado**: Utiliza la librería `pandas_ta` para calcular indicadores y generar señales de "Compra", "Venta" o "Mantener".

- **Visualización de Datos**: Genera y envía un gráfico creado con `matplotlib` que muestra el precio del activo, el Parabolic SAR y el Oscilador Estocástico para un análisis visual inmediato.

- **Extracción de Tickers**: Intenta identificar símbolos de activos (tickers) en los mensajes de los usuarios mediante expresiones regulares.

- **Registro de Consultas**: Almacena un historial de las consultas y las respuestas generadas en un archivo `consultas_bot.csv` para seguimiento y análisis de uso.

## 🔧 Instalación y Puesta en Marcha

Sigue estos pasos para configurar y ejecutar tu propia instancia de Bob the Bot.

### Prerrequisitos

- Python 3.8 o superior.
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

Abre el archivo `config.py` y reemplaza el texto del marcador de posición con el token que obtuviste.

```python
# config.py
TELEGRAM_BOT_TOKEN = "AQUÍ_VA_TU_TOKEN_SECRETO"
```

### 6. Ejecutar el Bot

Una vez instalado y configurado, inicia el bot con el siguiente comando, que ejecuta el archivo `main.py`:

```bash
python main.py
```

Si todo está correcto, verás el mensaje `Bot iniciado. Presiona Ctrl+C para detener.` en tu terminal. ¡Tu bot ya está en línea!

## 📁 Estructura del Proyecto

- **`main.py`**: Punto de entrada que inicia la ejecución del bot.

- **`bot_logic.py`**: Contiene toda la lógica de Telegram: manejo de comandos, procesamiento de mensajes, orquestación del análisis y envío de respuestas.

- **`config.py`**: Almacena configuraciones sensibles, como el token del bot de Telegram.

- **`data_provider.py`**: Se encarga de obtener los datos históricos y el precio actual de los activos financieros utilizando la librería `yfinance`.

- **`technical_analysis.py`**: Realiza los cálculos de los indicadores técnicos (Parabolic SAR y Oscilador Estocástico) para generar las señales.

- **`query_logger.py`**: Gestiona el registro de todas las consultas de los usuarios en un archivo CSV para su posterior análisis.

- **`requirements.txt`**: Lista las dependencias de Python necesarias para que el proyecto funcione correctamente.

## ⚖️ Descargo de Responsabilidad

Este bot es una herramienta creada con fines educativos y de demostración. Los análisis que proporciona se basan únicamente en datos históricos e indicadores técnicos automatizados. **Esta información no constituye asesoramiento financiero**. Siempre debes realizar tu propia investigación y considerar múltiples factores antes de tomar cualquier decisión de inversión.

## 📋 Uso del Bot

Una vez que el bot esté funcionando, puedes interactuar con él de varias maneras:

- Envía comandos directos como `/analizar AAPL`
- Haz preguntas en lenguaje natural como "¿Qué opinas de Tesla?"
- El bot identificará automáticamente los símbolos de acciones en tus mensajes
- Recibirás un análisis técnico junto con un gráfico visual

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Si encuentras algún error o tienes ideas para mejorar el bot, no dudes en abrir un issue o enviar un pull request.

## 📝 Licencia

Este proyecto es de libre acceso
