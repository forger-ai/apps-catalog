# AGENTS

## Fuente de Verdad

Este repo contiene el catálogo público de apps que lee la aplicación desktop de Forger.

El catálogo no es la fuente principal de implementación de las apps. Cada app mantiene su código, releases, CI e historial en su propio repositorio. Este repo contiene la metadata publicada y aprobada que permite a la desktop descubrir, descargar e instalar apps.

Cuando un repo de app publica una nueva versión, su workflow de release abre un PR contra este repo para actualizar el manifest de esa app dentro del catálogo. Al aprobarse y mergearse ese PR, el workflow de catálogo regenera `catalog.json` y lo publica en GitHub Pages.

## Rol del Catálogo

El catálogo es el contrato publicado entre apps instalables y la app desktop.

La desktop usa el catálogo para saber:

- qué apps están disponibles;
- qué versión está publicada;
- qué stack runtime usa cada app;
- qué plataformas soporta;
- qué permisos declara;
- desde qué URL descarga el ZIP instalable;
- qué checksum, tamaño y fecha de publicación corresponden al ZIP cuando están disponibles;
- qué metadata visible debe mostrar al usuario.

El catálogo no debe inventar capacidades de producto. Las capacidades visibles de cada app se documentan en el `AGENTS.md` y documentación interna del repo de esa app.

## Estructura Actual

```text
{stack-name}/
  commons/      Copia publicada de piezas compartidas del stack cuando aplica
  skeleton/     Base publicada del stack cuando aplica
  {app-name}/   Metadata publicada de una app instalable

scripts/
  generate_catalog.py   Genera catalog.json desde manifests y metadata de releases
  build_setup.sh        Herramienta interna para preparar commons en estructura de compatibilidad
  build_check.sh        Herramienta interna de verificación
  build_package.sh      Herramienta interna de empaquetado de compatibilidad

.github/
  workflows/
    catalog.yml         Genera catalog.json y publica GitHub Pages
    validate.yml        Valida cambios del catálogo
```

El stack publicado actualmente es `vite-fastapi-sqlite`.

La app publicada actualmente en ese stack es `finance-os`.

## Flujo de Publicación Actual

El flujo de publicación de una app hacia el catálogo funciona así:

1. La app vive y se desarrolla en su propio repositorio.
2. La app define su metadata en `manifest.json`.
3. La app define en `catalog.release` el repo de release, formato de tag, nombre del asset ZIP, repo del catálogo y ruta del manifest dentro del catálogo.
4. Al publicarse una release/tag válida, el workflow del repo de la app verifica backend y frontend.
5. El workflow construye el ZIP instalable.
6. El workflow calcula checksum, tamaño y fecha de publicación.
7. El workflow sube el ZIP al GitHub Release de la app.
8. El workflow hace checkout de este repo de catálogo.
9. El workflow actualiza el manifest publicado de la app en la ruta configurada.
10. El workflow abre un PR automático contra `main`.
11. Una persona o agente revisa el PR.
12. Al mergearse el PR, `catalog.yml` genera `catalog.json`.
13. GitHub Pages publica el `catalog.json`.
14. La app desktop lee el catálogo publicado.

La aprobación del PR es el punto de control del catálogo. Una release de app no queda disponible para la desktop hasta que el cambio correspondiente entra al catálogo publicado.

## `manifest.json`

Cada app publicada en el catálogo tiene un `manifest.json` en su carpeta de app.

Campos funcionales relevantes:

- `name`: slug técnico estable de la app.
- `version`: versión publicada que la desktop considera disponible.
- `description`: descripción general de la app.
- `changelog`: lista de cambios visibles por versión publicada.
- `stack`: metadata del backend, frontend, base de datos y versiones requeridas.
- `catalog.display_name`: nombre visible en catálogo.
- `catalog.short_description`: resumen corto.
- `catalog.description`: descripción visible más completa.
- `catalog.category`: categoría visible.
- `catalog.permissions`: permisos declarados para la app.
- `catalog.supported_platforms`: plataformas soportadas.
- `catalog.release.repository`: repo donde vive el GitHub Release con el ZIP.
- `catalog.release.tag_template`: formato del tag publicado.
- `catalog.release.asset_name_template`: formato del ZIP publicado.
- `catalog.release.checksum_sha256`: checksum del ZIP publicado cuando está registrado.
- `catalog.release.file_size_bytes`: tamaño del ZIP publicado cuando está registrado.
- `catalog.release.published_at`: fecha de publicación cuando está registrada.

El manifest puede contener servicios, scripts y skills. Esos campos ayudan a la desktop y al agente a operar la app instalada. No son una lista de capacidades visibles para usuario final.

## `catalog.json`

`scripts/generate_catalog.py` lee los manifests publicados bajo carpetas de stack y genera `catalog.json`.

La salida contiene una lista de apps con:

- `slug`;
- `name`;
- `short_description`;
- `description`;
- `category`;
- `runtime_stack`;
- `latest_version`.

`latest_version` contiene metadata de instalación:

- `version`;
- `runtime_stack`;
- versiones requeridas de Python y Node;
- plataformas soportadas;
- permisos;
- URL de descarga;
- tamaño;
- checksum;
- fecha de publicación.
- changelog de la versión publicada cuando está declarado.

El script intenta leer metadata del GitHub Release usando `gh release view`. Si hay asset esperado configurado, la URL de descarga se resuelve con el repo, tag y nombre del asset.

## Reglas Para Agentes

- Tratar este repo como catálogo publicado, no como repo principal de desarrollo de apps.
- No modificar código de producto de una app dentro del catálogo si el cambio pertenece al repo fuente de esa app.
- Para cambios funcionales de una app, trabajar en el repo de la app y dejar que su release actualice el catálogo por PR.
- En este repo, revisar especialmente manifests, metadata de release, checksums, versiones, permisos y consistencia del catálogo.
- No presentar `manifest.json`, scripts ni workflows como interfaz normal para usuarios finales.
- Describir hacia usuario final solo el impacto visible: app disponible, versión, descripción, permisos y estado de publicación.
- No afirmar que una app está disponible en desktop si el PR de catálogo no está mergeado y publicado.
- No inventar capacidades de una app desde textos de marketing del catálogo; validar contra el repo de la app y su `AGENTS.md`.
- Si una carpeta de app dentro del catálogo contiene código copiado, tratarlo como snapshot publicado o estructura de compatibilidad, no como fuente principal de verdad.

## Reglas de Cambios

Cambios apropiados en este repo:

- actualizar manifest publicado de una app;
- revisar metadata de release;
- corregir datos visibles del catálogo;
- ajustar generación de `catalog.json`;
- ajustar validaciones del catálogo;
- mantener documentación de catálogo.

Cambios que pertenecen al repo de la app:

- modificar backend;
- modificar frontend;
- modificar base de datos;
- modificar scripts operativos de app;
- modificar skills de app;
- cambiar capacidades funcionales;
- cambiar documentación funcional específica de una app.

## Comunicación

Usar lenguaje simple cuando el usuario pregunte por el catálogo.

Explicar el catálogo como la lista publicada de apps que la desktop puede instalar.

Evitar detalles internos salvo que el usuario los pida explícitamente.

Cuando se hable con un usuario final:

- decir "la app está disponible en el catálogo" solo si está publicada;
- decir "hay una actualización pendiente de aprobación" si existe un PR no mergeado;
- decir "la desktop descarga la app desde la versión publicada" en vez de explicar GitHub Releases, assets y manifests.
