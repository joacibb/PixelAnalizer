# PixelAnalizer — Análisis Científico de Cobertura Terrestre 🛰️

PixelAnalizer es una herramienta profesional de procesamiento de imágenes satelitales diseñada para la clasificación granular de cobertura terrestre (Land Cover Analysis). Permite a investigadores y técnicos realizar inspecciones espaciales precisas, delimitar áreas de interés (ROI) y exportar datos estadísticos para análisis institucional (NASA, INVAP, etc.).

---

## ✨ Características Principales

### 🔬 Análisis Científico
- **Clasificación Automática**: Identificación de Vegetación (Densa, Media, Escasa), Suelos Áridos, Cuerpos de Agua y Nubes/Nieve.
- **Calibración Dinámica**: Los rangos de detección (HSV) son completamente configurables mediante archivos YAML sin necesidad de modificar el código.
- **Detección Dual**: Manejo avanzado de matices (como el espectro rojo circular) para evitar errores comunes de detección en OpenCV.

### 📐 Herramientas de Interacción
- **Region of Interest (ROI)**: Selector de área mediante clic y arrastre para analizar parcelas específicas ignorando zonas irrelevantes o nubes.
- **Puntero de Inspección**: Herramienta técnica para obtener valores exactos de RGB, HSV y clase asignada de cualquier píxel individual.
- **Filtrado Interactivo**: Hacé clic en cualquier resultado estadístico para visualizar instantáneamente solo los píxeles pertenecientes a esa categoría.

### 🚀 Arquitectura Profesional
- **Modularidad**: Código desacoplado siguiendo principios SOLID (Core Engine, UI Components, Utils).
- **Exportación de Datos**: Generación de reportes en formatos **CSV** y **JSON** listos para integrar en flujos de trabajo científicos.
- **Logging Robusto**: Registro detallado de operaciones y errores en archivos de texto para trazabilidad.

---

## 📂 Estructura del Proyecto

```text
PixelAnalizer/
├── config/             # Configuración de rangos de color (YAML)
├── src/
│   ├── core/           # Motor de análisis y carga de imágenes
│   ├── ui/             # Interfaz gráfica (Tkinter/PIL)
│   └── utils/          # Logging, exportación y utilidades
├── tests/              # Suite de pruebas automatizadas
├── logs/               # Registros de ejecución
├── exports/            # Resultados de análisis (CSV/JSON)
├── main.py             # Punto de entrada de la aplicación
└── requirements.txt    # Dependencias del proyecto
```

---

## 🛠️ Instalación y Uso

### 1. Requisitos Previos
- Python 3.10 o superior.
- Dependencias del sistema (Linux): `sudo dnf install python3-pillow-tk` (o equivalente en tu distro).

### 2. Instalación
Cloná el repositorio y cargá las dependencias:
```bash
pip install -r requirements.txt
```

### 3. Ejecución
```bash
python main.py
```

### 4. Pruebas Automatizadas
Para verificar la integridad del motor de cálculo:
```bash
pytest tests/ -v
```

---

## ⚙️ Configuración Personalizada

Podés ajustar la sensibilidad de la detección en `config/color_ranges.yaml`. Ejemplo:
```yaml
high_vegetation:
  display_name: "Vegetación Densa"
  hue_lower1: 45
  hue_upper1: 85
  sat_min: 60
  val_min: 30
```

---

## 🔓 Open Source & Licencia

Este proyecto es **Open Source** y está distribuido bajo la licencia **MIT**. 

- **Uso Libre**: Podés usarlo, modificarlo y distribuirlo gratuitamente para fines personales, educativos o comerciales.
- **Contribuciones**: ¡Las contribuciones son bienvenidas! Si tenés mejoras para los algoritmos de detección o la UI, no dudes en abrir un *Pull Request*.

---
*Desarrollado y refactorizado profesionalmente para el análisis geoespacial avanzado.*