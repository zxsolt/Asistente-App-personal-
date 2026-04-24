# Coolify Deploy Design

## Objetivo

Desplegar la aplicacion como un unico servicio en Coolify, con una sola URL publica y persistencia local de SQLite para uso personal.

## Arquitectura

- Un contenedor Docker multi-stage
- `frontend` compilado con Vite
- `backend` FastAPI servido por `uvicorn`
- `nginx` como servidor frontal y proxy inverso
- SQLite persistida en `/data/planner.db`

## Decisiones

- Se usa un solo servicio porque reduce configuracion en Coolify
- `nginx` sirve la SPA y reenvia `/api/*` al backend interno
- El frontend consume `/api` por defecto para evitar variables extra en produccion
- `DATABASE_URL` apunta por defecto a `/data/planner.db`, pensada para un volumen persistente

## Operacion en Coolify

- Build desde `Dockerfile`
- Puerto interno `80`
- Variable obligatoria `SECRET_KEY`
- Volumen persistente montado en `/data`
- Healthcheck recomendado en `/health`

## Riesgos y limites

- SQLite es suficiente para uso personal, pero no para alta concurrencia
- El backend mantiene `create_all` al arrancar; para evolucionar esquema de forma estricta conviene migrar con Alembic
- Si no se monta `/data`, la base se perdera al recrear el contenedor
