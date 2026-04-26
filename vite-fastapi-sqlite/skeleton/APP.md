# APP

## Identidad
- id: skeleton
- nombre: Skeleton
- version: 0.1.0
- tipo: plantilla base para apps Forger

## Objetivo funcional
Skeleton es una app de ejemplo para iniciar proyectos nuevos con backend y frontend listos.
Su objetivo es validar que la conexion entre frontend y API funcione y sirva como base para nuevas features.

## Usuario objetivo
- Equipos que quieren crear una app nueva rapido.
- Usuarios no tecnicos que solo necesitan confirmar que la app esta "viva".

## Stack
- Backend: Python 3.12 + FastAPI
- Frontend: Vite + React + MUI

## Servicios
- Backend HTTP
  - base: `http://localhost:8000`
  - docs: `/api/docs`
  - openapi: `/api/openapi.json`
- Frontend HTTP
  - base: `http://localhost:5173`

## Endpoints API actuales
- `GET /api/health`
  - Respuesta esperada: `{"status":"ok","version":"0.1.0"}`

## Flujo funcional principal
1. Abrir frontend.
2. Frontend consulta `GET /api/health`.
3. Mostrar estado de conexion con la API.

## Variables relevantes
- `VITE_API_BASE_URL` (frontend): URL base de la API.

## Notas para agentes
- Esta app es una base minima: no asumir reglas de negocio complejas.
- Antes de agregar features, definir primero el flujo funcional esperado.
- Mantener mensajes y pantallas en lenguaje simple para usuarios no tecnicos.
