# 00 · Guía General del Proyecto

## Centro Cultural Inteligente

Este documento explica el sistema completo, del navegador a la base de datos, para que cualquier integrante del equipo entienda el panorama antes de estudiar su capa específica.

---

## 1. ¿Qué hace la aplicación?

Permite registrar visitantes de eventos especiales del Centro Cultural. Cada visitante tiene **nombre**, **correo** y **categoría** (General, Estudiante, Adulto mayor, VIP). Se pueden crear, listar en tiempo real, editar y eliminar registros. La información se guarda de forma permanente en PostgreSQL.

## 2. Las cuatro capas

| Capa | Tecnología | Responsable | Función |
| ---- | ---------- | ----------- | ------- |
| Presentación | HTML/CSS/JS | Integrante A (Frontend) | Formulario y tabla en el navegador |
| Lógica / API | Flask + Gunicorn | Integrante B (Backend) | Reglas de negocio y CRUD |
| Datos | PostgreSQL 16 | Integrante C (DB/SRE) | Almacenamiento persistente |
| Infraestructura | Nginx + Docker + CI/CD + AWS | Integrante D (DevOps) | Puerta de entrada, orquestación y despliegue |

## 3. Recorrido de una petición (crear un visitante)

1. El usuario llena el formulario en `http://<servidor>/` y pulsa **Registrar**.
2. `app.js` ejecuta `fetch("/api/visitantes", { method: "POST", ... })` usando una **ruta relativa**.
3. La petición llega a **Nginx** en el puerto 80.
4. Nginx ve el prefijo `/api/` y la reenvía a `http://backend:5000` (red interna de Docker).
5. **Flask** (servido por Gunicorn) recibe el POST, valida los datos con `validation.py`.
6. `db.py` abre una conexión a **PostgreSQL** y ejecuta un `INSERT` **parametrizado** dentro de una transacción.
7. PostgreSQL guarda la fila en su directorio de datos, que es un **bind mount** al disco del host (EBS en AWS).
8. Flask responde `201 Created` con el visitante en JSON.
9. Nginx devuelve la respuesta al navegador.
10. `app.js` muestra un mensaje de éxito y **refresca solo la tabla** (sin recargar la página).

## 4. ¿Por qué esta arquitectura?

- **Un solo punto de entrada (Nginx, puerto 80)**: reduce la superficie de ataque.
- **Mismo origen (frontend + API por Nginx)**: elimina los problemas de CORS.
- **PostgreSQL en red privada**: la base de datos nunca es accesible desde Internet.
- **Bind mount / EBS**: los datos sobreviven a la destrucción de contenedores.
- **CI/CD con GitHub Actions**: cada cambio en `main` se despliega automáticamente y de forma verificable.

## 5. Redes de Docker

- `public_network`: conecta Nginx con el backend.
- `private_network` (marcada como `internal`): conecta el backend con PostgreSQL y **no tiene salida a Internet**.
- El backend pertenece a ambas redes; PostgreSQL solo a la privada; Nginx solo a la pública.

## 6. Persistencia en una frase

Los datos viven en el disco del host (bind mount respaldado por EBS), no dentro del contenedor; por eso `docker compose down` elimina los contenedores pero **no** los datos.

## 7. Flujo de trabajo del equipo (Git Flow)

Cada integrante trabaja en su rama (`feature/...`), nadie hace commits directos a `main`, y toda integración pasa por un Pull Request. Detalle en [`06_GUIA_GITHUB_GIT_FLOW.md`](06_GUIA_GITHUB_GIT_FLOW.md).

## 8. Mapa de documentos

| Documento | Para quién |
| --------- | ---------- |
| `01_DEFENSA_FRONTEND.md` | Integrante A |
| `02_DEFENSA_BACKEND.md` | Integrante B |
| `03_DEFENSA_DATABASE_SRE.md` | Integrante C |
| `04_DEFENSA_DEVOPS.md` | Integrante D |
| `05_GUIA_DESPLIEGUE_AWS.md` | Todos (despliegue) |
| `06_GUIA_GITHUB_GIT_FLOW.md` | Todos (Git) |
| `07_PLAN_PRUEBAS_AUDITORIA.md` | Todos (pruebas) |
| `08_EVIDENCIAS_PDF.md` | Todos (evidencias) |
| `09_PREGUNTAS_Y_RESPUESTAS_DEFENSA.md` | Todos (defensa) |
| `10_CHECKLIST_RUBRICA.md` | Todos (rúbrica) |
| `11_REPORTE_FINAL_AUDITORIA.md` | Todos (cierre) |
