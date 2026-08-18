# Tarjetas de inglés — Sistema Leitner (versión corregida)

## Completamente hecho por vibe code con ChatGPT Pro 17SAUG2026 - El codigo no fue revisado.
## Publicación

Sube estos dos archivos a la misma carpeta pública:

- `index.html`
- `vocabulary.csv`

El nombre debe ser exactamente `vocabulary.csv`, en minúsculas.

## Cómo carga el vocabulario

1. Cuando la página se sirve desde un sitio web, primero intenta cargar el archivo `vocabulary.csv` que está al lado de `index.html`.
2. El archivo se vuelve a comprobar en cada apertura para que los cambios publicados se incorporen. El progreso de las tarjetas que no cambian se conserva.
3. Si el servidor, una ruta sin barra final o las reglas del navegador impiden leer ese archivo, `index.html` contiene una copia integrada del vocabulario actual como respaldo. Por eso la pantalla “Elegir archivo CSV” no debe aparecer en el uso normal.
4. Si el usuario carga deliberadamente otro CSV desde “Administrar”, ese archivo manual permanece seleccionado en ese navegador.

## Abrir la página directamente desde una carpeta

Los navegadores suelen bloquear `fetch()` entre archivos abiertos con direcciones `file://`. Esta versión detecta ese caso y usa automáticamente la copia integrada. No requiere seleccionar el CSV.

## Vocabulario incluido

El archivo suministrado contiene 684 tarjetas, todas inicialmente en la Caja de espera. El estudiante utiliza el botón para añadir hasta cinco tarjetas a la Caja 1.

## Actualizar el vocabulario

En un sitio web, reemplaza `vocabulary.csv` y conserva el nombre exacto. Si el servicio de alojamiento utiliza caché, publica nuevamente o limpia su caché. La página solicita el CSV con `cache: no-store`.

La copia integrada es un respaldo del CSV incluido en este paquete. Para cambiar también esa copia cuando se usa la página mediante `file://`, utiliza la opción “Cargar otro CSV” o genera un nuevo `index.html` con el vocabulario actualizado.
