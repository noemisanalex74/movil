# Instrucciones para el Laboratorio 3D (AGP_3D_Generator_v2)

Este documento explica cómo utilizar el notebook de Google Colab `AGP_3D_Generator_v2.ipynb` para generar vistas 360° de un objeto a partir de una sola imagen.

**IMPORTANTE:** Este proceso se ejecuta en la nube de Google, no en tu dispositivo local. Necesitas una cuenta de Google.

---

## Requisitos Previos

1.  **Cuenta de Google:** Necesaria para usar Google Drive y Google Colab.
2.  **Navegador Web:** Para interactuar con las herramientas de Google.

---

## Paso 1: Configurar la Estructura de Carpetas en Google Drive

El notebook necesita una estructura de carpetas específica en tu Google Drive para funcionar.

1.  Abre tu [Google Drive](https://drive.google.com).
2.  Crea una carpeta principal llamada `AGP_Dashboard`.
3.  Dentro de `AGP_Dashboard`, crea otra carpeta llamada `3D_Lab`.
4.  Dentro de `3D_Lab`, crea dos carpetas:
    *   `Entrada`: Aquí es donde subirás las imágenes que quieres procesar.
    *   `Salida`: Aquí es donde el notebook guardará las imágenes 360° generadas.

La estructura final debe ser: `Mi unidad > AGP_Dashboard > 3D_Lab > Entrada`

---

## Paso 2: Subir y Ejecutar el Notebook en Google Colab

1.  **Sube el Notebook:**
    *   Ve a tu Google Drive.
    *   Sube el archivo `AGP_3D_Generator_v2.ipynb` a cualquier carpeta (por ejemplo, dentro de `AGP_Dashboard`).

2.  **Abre el Notebook en Colab:**
    *   Haz doble clic en el archivo `AGP_3D_Generator_v2.ipynb` en tu Google Drive.
    *   Si te lo pide, selecciona "Abrir con Google Colaboratory".

3.  **Ejecuta las Celdas:**
    *   El notebook está dividido en celdas de código. Debes ejecutarlas en orden.
    *   Para ejecutar una celda, haz clic en el botón de "Play" (un círculo con un triángulo) que aparece a la izquierda de la celda.
    *   **Celda 1: Configuración y Conexión:**
        *   Ejecútala. Te pedirá permiso para acceder a tu Google Drive. Acepta para continuar.
    *   **Celda 2: Instalación de Dependencias:**
        *   Ejecútala. Esta celda puede tardar **varios minutos** en completarse, ya que descarga el modelo de IA y las librerías necesarias.
    *   **Celda 3: Cargar Modelo y Definir Funciones:**
        *   Ejecútala. Carga el modelo en la memoria. También puede tardar un poco la primera vez.
    *   **Celda 4: Iniciar el Bucle de Procesamiento:**
        *   Antes de ejecutarla, **sube una imagen** (por ejemplo, `mi_objeto.png`) a la carpeta `Entrada` que creaste en Google Drive.
        *   Ahora sí, ejecuta esta celda. El script empezará a buscar imágenes en la carpeta `Entrada`.

---

## Paso 3: Verificar los Resultados

1.  **Revisa la Salida del Notebook:** La celda 4 te mostrará mensajes indicando que ha encontrado tu imagen, la está procesando y ha guardado las vistas.
2.  **Revisa tu Google Drive:** Ve a la carpeta `Mi unidad > AGP_Dashboard > 3D_Lab > Salida`.
3.  Deberías encontrar varias imágenes nuevas, como `mi_objeto_view_0.png`, `mi_objeto_view_60.png`, etc. Estas son las vistas 360° de tu objeto.
4.  La imagen original habrá sido movida a una nueva carpeta `Procesadas` dentro de `Entrada`.

Si ves estas imágenes, **¡el sistema funciona correctamente!**

---

## Siguientes Pasos (Plan de Futuro)

El estado actual es una **Prueba de Concepto (PoC)**. El siguiente gran paso es tomar estas vistas 2D y convertirlas en un verdadero modelo 3D.

1.  **Investigar y Desarrollar la Reconstrucción 3D:** Investigar técnicas y herramientas (como NeRF o Gaussian Splatting) para combinar las vistas 2D en un archivo de modelo 3D (como `.glb` o `.obj`).
2.  **Automatizar el Proceso Completo:** Modificar el notebook para que, después de generar las vistas, inicie automáticamente el proceso de reconstrucción 3D.
3.  **Integración con el Dashboard:** Explorar formas de iniciar este proceso y visualizar los resultados directamente desde el AGP-Dashboard web.
