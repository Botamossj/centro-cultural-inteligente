# 06 · Guía de GitHub y Git Flow

Guía para que los **cuatro integrantes** colaboren correctamente: cada uno en su rama, sin commits directos a `main`, e integrando todo mediante Pull Requests.

> **Regla ética y de auditoría:** cada integrante debe ejecutar **sus propios commits desde su propia cuenta de GitHub y su propia máquina**. No se crean commits falsos ni autorías compartidas. El código puede existir localmente, pero cada persona debe recrear/aportar los cambios de su capa en su rama real.

---

## 1. Crear el repositorio en GitHub
**Opción web:** GitHub → **New repository** → nombre `centro-cultural-inteligente` → privado → **Create repository**.

**Opción CLI:**
```bash
gh auth login
gh repo create centro-cultural-inteligente --private --source=. --remote=origin --push
```

## 2. Añadir colaboradores
GitHub → repositorio → **Settings → Collaborators → Add people** → invitar a los otros tres integrantes por su usuario de GitHub. Cada uno acepta la invitación.

## 3. Configurar la identidad Git real (cada integrante en su máquina)
```bash
git config --global user.name "Nombre Real"
git config --global user.email "correo-de-github@example.com"
```
> El correo debe coincidir con el de su cuenta de GitHub para que los commits se atribuyan correctamente en el grafo de contribuciones.

## 4. Clonar el repositorio (cada integrante)
```bash
git clone https://github.com/USUARIO/centro-cultural-inteligente.git
cd centro-cultural-inteligente
```

## 5. Crear la rama asignada (cada integrante)
```bash
git checkout main
git pull origin main
git checkout -b feature/frontend    # o feature/backend, feature/database, feature/devops
```

## 6. Cada integrante hace commits solo de SU trabajo
Trabajar únicamente en los archivos de su capa (ver sección "Commits sugeridos") y confirmar:
```bash
git add <solo-mis-archivos>
git commit -m "feat(frontend): formulario de registro de visitantes"
```

## 7. Commits sugeridos por rol
**Frontend (`feature/frontend`):**
```bash
git add frontend/index.html
git commit -m "feat(frontend): estructura HTML del formulario y la tabla"
git add frontend/styles.css
git commit -m "style(frontend): diseño responsivo y accesible"
git add frontend/app.js
git commit -m "feat(frontend): consumo de la API con Fetch y render seguro"
```
**Backend (`feature/backend`):**
```bash
git add backend/requirements.txt backend/db.py
git commit -m "feat(backend): conexión a PostgreSQL con reintentos y transacciones"
git add backend/validation.py
git commit -m "feat(backend): validación y normalización de datos"
git add backend/app.py
git commit -m "feat(backend): endpoints CRUD y health check"
git add backend/Dockerfile
git commit -m "chore(backend): imagen con Gunicorn y usuario no root"
```
**Base de datos / SRE (`feature/database`):**
```bash
git add database/schema.sql
git commit -m "feat(database): esquema, constraints e índices de visitantes"
git add scripts/test_persistence.sh scripts/verify_hardening.sh
git commit -m "test(database): pruebas de persistencia y hardening"
```
**DevOps (`feature/devops`):**
```bash
git add nginx/nginx.conf
git commit -m "feat(devops): Nginx como API Gateway"
git add docker-compose.yml
git commit -m "feat(devops): orquestación con redes y health checks"
git add .github/workflows/deploy.yml
git commit -m "ci(devops): pipeline de validación y despliegue a EC2"
```

## 8. Subir la rama
```bash
git push -u origin feature/frontend    # cada quien su rama
```

## 9. Abrir un Pull Request
**Web:** GitHub muestra "Compare & pull request" → base `main`, compare `feature/...` → título y descripción → **Create pull request**.

**CLI:**
```bash
gh pr create --base main --head feature/frontend \
  --title "feat(frontend): interfaz de registro de visitantes" \
  --body "Implementa el frontend responsivo y su integración con la API."
```

## 10. Revisar un Pull Request
- Otro integrante abre la pestaña **Files changed**, comenta y aprueba (**Approve**).
- Se recomienda al menos **1 aprobación** antes de mergear.

## 11. Merge sin commits directos a `main`
Desde la página del PR → **Merge pull request** → **Confirm merge**. Nunca se hace `git push origin main` directamente.

## 12. Resolver conflictos de merge
```bash
git checkout feature/mi-rama
git fetch origin
git merge origin/main          # trae los cambios ya integrados en main
# Editar los archivos en conflicto (marcas <<<<<<< ======= >>>>>>>)
git add <archivos-resueltos>
git commit                     # confirma la resolución
git push
```

## 13. Verificar el grafo de contribuciones
- GitHub → repositorio → **Insights → Contributors** y **Network**.
- Debe verse que los cuatro integrantes tienen commits en sus ramas y que todo entró por PRs.

## 14. Activar la protección de la rama `main`
GitHub → **Settings → Branches → Add branch protection rule**:
- Branch name pattern: `main`.
- ☑ Require a pull request before merging.
- ☑ Require approvals (mínimo 1).
- ☑ Do not allow bypassing the above settings.

## 15. Impedir pushes directos a `main`
La regla anterior lo garantiza: con "Require a pull request before merging", GitHub rechaza cualquier `git push origin main` directo. Todo cambio debe pasar por un PR aprobado.

---

## Orden recomendado de integración
1. `feature/database` (base) → PR → merge.
2. `feature/backend` → PR → merge.
3. `feature/frontend` → PR → merge.
4. `feature/devops` (integración final) → PR → merge.

Tras cada merge a `main`, GitHub Actions despliega automáticamente a EC2.
