# Asistente App Personal

Aplicacion personal con:

- `backend/`: FastAPI + SQLAlchemy + SQLite
- `frontend/`: React + Vite

## Despliegue en Coolify

El proyecto queda preparado para desplegarse como `Dockerfile` en un solo servicio.

### Configuracion recomendada

- Tipo: `Dockerfile`
- Puerto interno: `80`
- Volumen persistente: montar `/data`
- Variable obligatoria: `SECRET_KEY`

### Variables opcionales

- `DATABASE_URL`
  - Por defecto usa `sqlite+aiosqlite:////data/planner.db`
  - Si no la cambias y montas `/data`, la base queda persistida

### Healthcheck

- Ruta recomendada: `/health`

### Flujo de red

- `Nginx` sirve el frontend compilado
- Las peticiones ` /api/* ` se proxifican al backend FastAPI interno
- El frontend usa `/api` por defecto, asi que no hace falta configurar `VITE_API_URL` para Coolify

## Desarrollo local

Backend:

```bash
./start_backend.sh
```

Frontend:

```bash
./start_frontend.sh
```
