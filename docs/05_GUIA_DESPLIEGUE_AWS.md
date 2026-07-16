# 05 · Guía de Despliegue en AWS EC2

Guía paso a paso para desplegar el Centro Cultural Inteligente en una instancia **AWS EC2 (Ubuntu)** con almacenamiento **EBS**, PostgreSQL autogestionada y despliegue automático por GitHub Actions.

> No se usa ninguna base de datos gestionada (RDS). PostgreSQL corre en un contenedor con persistencia en el disco EBS de la instancia.

---

## 1. Crear la instancia EC2
1. Consola de AWS → **EC2** → **Launch instance**.
2. Nombre: `centro-cultural`.
3. AMI: **Ubuntu Server 22.04 LTS** (o 24.04).
4. Tipo: `t2.micro` o `t3.small` (suficiente para el proyecto).
5. Par de claves: crear o seleccionar uno (`.pem`) para acceso SSH.
6. Almacenamiento: dejar el volumen **EBS** raíz (mínimo 8–20 GB). Aquí vivirán los datos.
7. Configurar el **Security Group** (ver sección 11).
8. Lanzar la instancia y anotar su **IP pública**.

## 2. Preparar Ubuntu
Conéctate por SSH:
```bash
ssh -i mi-clave.pem ubuntu@<IP_PUBLICA>
```
Actualiza el sistema:
```bash
sudo apt update && sudo apt upgrade -y
```

## 3. Instalar Docker y Docker Compose
```bash
# Docker Engine + plugin de Compose (repositorio oficial)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Permitir usar docker sin sudo
sudo usermod -aG docker $USER
newgrp docker

# Verificar
docker --version
docker compose version
```

## 4. Instalar Git
```bash
sudo apt install -y git
git --version
```

## 5. Preparar las claves SSH para el despliegue
GitHub Actions se conectará a EC2 con una clave dedicada.
```bash
# En tu máquina local o en el servidor, genera un par SOLO para deploy:
ssh-keygen -t ed25519 -C "github-actions-deploy" -f deploy_key

# Copia la clave PÚBLICA al servidor (authorized_keys del usuario de deploy):
cat deploy_key.pub >> ~/.ssh/authorized_keys   # ejecutar en el servidor
```
La clave **privada** (`deploy_key`) se guardará como secreto `SSH_PRIVATE_KEY` en GitHub (ver sección 12). Nunca la subas al repositorio.

## 6. Crear el directorio de la aplicación
```bash
sudo mkdir -p /opt/centro-cultural/app
sudo chown -R $USER:$USER /opt/centro-cultural
```

## 7. Explicación de la persistencia con EBS
- El volumen **EBS** es el disco de bloques persistente de la instancia EC2.
- Los datos de PostgreSQL se guardan en `/opt/centro-cultural/postgres-data`, que está en el sistema de archivos respaldado por EBS.
- El `docker-compose.yml` monta esa carpeta dentro del contenedor:
  `/opt/centro-cultural/postgres-data` → `/var/lib/postgresql/data`.
- Por eso, aunque destruyas y recrees los contenedores, **los datos permanecen** en EBS. Puedes incluso crear *snapshots* de EBS como copia de seguridad.

## 8. Clonar el repositorio
```bash
cd /opt/centro-cultural/app
git clone https://github.com/USUARIO/centro-cultural-inteligente.git .
```
> El punto final clona dentro del directorio actual.

## 9. Crear el archivo `.env` de producción
```bash
cp .env.example .env
nano .env
```
Configura valores reales (ejemplo):
```env
DB_NAME=centro_cultural
DB_USER=centro_user
DB_PASSWORD=UNA_CONTRASENA_LARGA_Y_SEGURA
DB_HOST=database
DB_PORT=5432
POSTGRES_DATA_PATH=/opt/centro-cultural/postgres-data
APP_ENV=production
```

## 10. Permisos del directorio de datos y primer despliegue
```bash
mkdir -p /opt/centro-cultural/postgres-data
docker compose up -d --build
docker compose ps
curl --fail http://localhost/api/health
```
Deberías ver los tres servicios y un health `200`.

## 11. Configurar el Security Group
| Puerto | Protocolo | Origen | Motivo |
| ------ | --------- | ------ | ------ |
| 80 | TCP | `0.0.0.0/0` | Acceso público a la app (Nginx) |
| 22 | TCP | **Tu IP** (`x.x.x.x/32`) | SSH restringido a IPs de confianza |
| 5432 | — | **NO abrir** | PostgreSQL nunca expuesta |
| 5000 | — | **NO abrir** | Backend nunca expuesto |

## 12. Configurar los GitHub Secrets
En GitHub → **Settings → Secrets and variables → Actions → New repository secret**:
| Secret | Valor |
| ------ | ----- |
| `SERVER_IP` | IP pública de la instancia EC2 |
| `SERVER_USER` | usuario SSH (ej. `ubuntu`) |
| `SSH_PRIVATE_KEY` | contenido completo de `deploy_key` (clave privada) |

O por CLI:
```bash
gh secret set SERVER_IP --body "<IP_PUBLICA>"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SSH_PRIVATE_KEY < deploy_key
```

## 13. Prueba pública
Desde tu navegador o desde otra máquina:
```bash
curl http://<IP_PUBLICA>/api/health
```
Abre `http://<IP_PUBLICA>` y registra un visitante.

## 14. Ver logs
```bash
docker compose logs --tail=100
docker compose logs backend
docker compose logs nginx
docker compose logs database
```

## 15. Reiniciar servicios
```bash
docker compose restart            # todos
docker compose restart backend    # uno
docker compose up -d --build      # recrear tras cambios
```

## 16. Recuperación tras un fallo
- **La app no responde**: `docker compose ps` y `docker compose logs`.
- **Un contenedor muere**: `restart: unless-stopped` lo reinicia solo; si no, `docker compose up -d`.
- **La instancia se reinicia**: Docker arranca los contenedores; los datos siguen en EBS.
- **Rollback de código**: `git reset --hard <commit_estable>` y `docker compose up -d --build`.
- **Copia de seguridad**: crear un *snapshot* de EBS desde la consola de AWS.

## 17. Verificación de hardening (desde otra máquina)
```bash
bash scripts/verify_hardening.sh <IP_PUBLICA>
```
Debe indicar que el puerto 5432 **no** es accesible.
