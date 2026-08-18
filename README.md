# Tarjetas de inglés — Sistema Leitner

Aplicación web móvil para estudiar vocabulario inglés–español mediante el sistema Leitner. La interfaz de estudio está en español y el lado inglés de las tarjetas no muestra texto: el estudiante escucha la palabra o frase en inglés mediante una grabación de audio.

> Desarrollado con ayuda de ChatGPT Pro. El código no ha sido sometido a una revisión formal independiente.

## Funciones principales

- Diseño **mobile-first** para teléfonos, tabletas y computadoras.
- Dos direcciones de práctica:
  - **Inglés → español:** escuchar el audio y luego revelar el texto en español.
  - **Español → inglés:** leer el texto en español, voltear la tarjeta y escuchar el audio en inglés.
- El texto inglés permanece oculto durante el ejercicio.
- Audio grabado con voz masculina **Microsoft Edge TTS `en-US-EricNeural` a -25 % de velocidad**.
- Voz generada por el navegador como respaldo si falta una grabación o el MP3 no puede reproducirse.
- Sistema Leitner de **cinco cajas**.
- **Caja de espera** para vocabulario todavía no introducido.
- Botón para añadir hasta **5 tarjetas a la Caja 1** cada vez.
- Tres evaluaciones por tarjeta:
  - **No la sabía:** vuelve a la Caja 1.
  - **Me costó:** permanece en la caja actual.
  - **La sabía:** avanza una caja.
- El progreso se guarda localmente en el navegador del estudiante.
- Importación y exportación de copia de seguridad del progreso.
- El progreso de tarjetas sin cambios se conserva al actualizar el vocabulario.

## Archivos necesarios para publicar

La raíz del sitio debe contener:

```text
english-flashcards/
├── index.html
├── vocabulary.csv
├── audio-manifest.json
└── audio/
    ├── 001-computer.mp3
    ├── 002-laptop.mp3
    ├── 003-desktop-computer.mp3
    ├── ...
    └── 684-tax-rate.mp3
```

También pueden existir otros archivos del repositorio, como `README.md` y `vocabulary-template.csv`; no afectan la aplicación.

## Vocabulario

`vocabulary.csv` contiene exactamente dos columnas:

```csv
English,Spanish
computer,computadora
laptop,portátil
```

El nombre del archivo debe ser exactamente:

```text
vocabulary.csv
```

La versión actual contiene **684 tarjetas**.

Las tarjetas nuevas comienzan en la **Caja de espera**. El estudiante las introduce a la práctica en grupos de hasta cinco mediante el botón correspondiente.

## Audio grabado

La carpeta `audio/` contiene un MP3 por entrada de vocabulario.

`audio-manifest.json` relaciona cada término inglés con su archivo MP3. La aplicación no intenta deducir el nombre del archivo a partir del texto; utiliza este manifiesto para evitar problemas con espacios, puntuación o caracteres especiales.

No se deben cambiar los nombres de los MP3 sin actualizar también `audio-manifest.json`.

La aplicación carga únicamente el audio que necesita y puede precargar la siguiente tarjeta. No descarga los 684 MP3 al abrir la página.

Si una grabación no existe, no aparece en el manifiesto o no puede reproducirse, la aplicación intenta utilizar `speechSynthesis` del navegador como respaldo.

## Dirección Español → inglés

En esta dirección:

1. El estudiante ve la palabra o frase en español.
2. Piensa cómo sonaría en inglés.
3. Voltea la tarjeta.
4. El lado inglés muestra solamente el botón de audio.
5. Al pulsar el botón se reproduce la grabación correspondiente.
6. El estudiante evalúa su respuesta.

La versión actual incluye una corrección específica para que el botón de audio funcione correctamente en la cara posterior de la tarjeta después de voltearla, especialmente en navegadores móviles.

## Dirección Inglés → español

En esta dirección:

1. El estudiante pulsa el botón de audio.
2. Escucha la palabra o frase en inglés sin verla escrita.
3. Piensa en el significado.
4. Voltea la tarjeta.
5. Ve la respuesta escrita en español.
6. Evalúa su respuesta.

## Sistema Leitner

La aplicación utiliza cinco cajas de estudio:

| Caja | Próxima revisión |
|---|---|
| 1 | Cada sesión |
| 2 | 1 día |
| 3 | 3 días |
| 4 | 7 días |
| 5 | 14 días |

Una respuesta **No la sabía** devuelve la tarjeta a la Caja 1. **Me costó** mantiene la tarjeta en su caja actual. **La sabía** la hace avanzar una caja, hasta un máximo de Caja 5.

## Caja de espera

Las tarjetas que todavía no han sido introducidas permanecen fuera de las cinco cajas Leitner en la **Caja de espera**.

El estudiante puede pulsar **Añadir 5 tarjetas a la Caja 1**. Si quedan menos de cinco, se añaden solamente las tarjetas restantes.

Las tarjetas de la Caja de espera no cuentan como pendientes ni tienen fecha de repaso hasta ser añadidas a la Caja 1.

## Cómo carga el vocabulario

Cuando la página se sirve desde GitHub Pages u otro servidor web, intenta cargar `vocabulary.csv` desde la misma carpeta que `index.html`.

El archivo se vuelve a comprobar al abrir la aplicación para que los cambios publicados puedan incorporarse. El progreso de las tarjetas cuyo inglés y español no hayan cambiado se conserva.

`index.html` también contiene una copia integrada del vocabulario como respaldo. Esto evita que aparezca normalmente la pantalla **Elegir archivo CSV** cuando el navegador no puede leer el archivo externo.

Si el usuario carga deliberadamente otro CSV desde la pantalla de administración, esa selección manual permanece guardada en ese navegador.

## Almacenamiento del progreso

El progreso se guarda en el almacenamiento local del navegador del estudiante. No hay cuentas de usuario ni base de datos en un servidor.

Por eso:

- actualizar `index.html` no debe borrar el progreso;
- reemplazar los MP3 no debe borrar el progreso;
- reemplazar `audio-manifest.json` no debe borrar el progreso;
- actualizar `vocabulary.csv` conserva el progreso de las tarjetas que siguen teniendo el mismo contenido inglés y español.

El estudiante puede exportar una copia de seguridad desde la aplicación y restaurarla posteriormente.

## Publicar en GitHub Pages usando solamente el navegador

Los archivos principales deben estar en la rama `main`, en la raíz del repositorio.

Para reemplazar `index.html`, `vocabulary.csv` o `audio-manifest.json`:

1. Abre el repositorio en GitHub.
2. Selecciona **Add file → Upload files**.
3. Sube el archivo actualizado.
4. Escribe un mensaje de commit.
5. Selecciona **Commit directly to the `main` branch**.
6. Pulsa **Commit changes**.

Para los MP3:

1. Entra primero en la carpeta `audio` del repositorio.
2. Selecciona **Add file → Upload files**.
3. Sube los archivos en grupos manejables; aproximadamente 50 por vez funciona bien.
4. Confirma que sigues dentro de `audio/` antes de cada carga.
5. Haz commit directamente a `main`.

GitHub Pages volverá a publicar el sitio cuando se actualice la rama configurada para la publicación.

## Después de una actualización

El navegador puede conservar una versión anterior de `index.html` en caché. En Windows, después de publicar una actualización, abre la página y utiliza:

```text
Ctrl + F5
```

Esto fuerza una recarga de los archivos publicados.

## Importante al cambiar el vocabulario o el audio

Si se añade o modifica vocabulario:

1. Actualiza `vocabulary.csv`.
2. Crea o reemplaza los MP3 correspondientes.
3. Actualiza `audio-manifest.json` para que coincida exactamente con esos archivos.
4. No cambies innecesariamente el texto inglés o español de tarjetas existentes si deseas conservar su historial de progreso.

## Tecnologías

La aplicación es completamente estática y no requiere instalación ni servidor de aplicaciones:

- HTML
- CSS
- JavaScript
- CSV
- JSON
- MP3
- Web Audio/HTML Audio
- Browser `speechSynthesis` como respaldo
- `localStorage` para el progreso

Puede publicarse directamente mediante GitHub Pages.