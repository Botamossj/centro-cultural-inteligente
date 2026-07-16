-- =====================================================================
-- Esquema de base de datos: Centro Cultural Inteligente
-- Motor: PostgreSQL 16
-- Este script se ejecuta automáticamente SOLO en el primer arranque
-- del contenedor (directorio /docker-entrypoint-initdb.d), cuando el
-- directorio de datos está vacío. Es idempotente gracias a IF NOT EXISTS.
-- =====================================================================

CREATE TABLE IF NOT EXISTS visitantes (
    id                  BIGSERIAL PRIMARY KEY,
    nombre              VARCHAR(120)  NOT NULL,
    correo              VARCHAR(150)  NOT NULL,
    categoria           VARCHAR(30)   NOT NULL,
    fecha_registro      TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT visitantes_correo_unique UNIQUE (correo),
    CONSTRAINT visitantes_categoria_check
        CHECK (categoria IN ('General', 'Estudiante', 'Adulto mayor', 'VIP'))
);

-- Índices para acelerar ordenamiento, búsqueda y filtrado.
CREATE INDEX IF NOT EXISTS idx_visitantes_fecha_registro
    ON visitantes (fecha_registro DESC);

CREATE INDEX IF NOT EXISTS idx_visitantes_nombre
    ON visitantes (nombre);

CREATE INDEX IF NOT EXISTS idx_visitantes_categoria
    ON visitantes (categoria);

-- ---------------------------------------------------------------------
-- Actualización automática de fecha_actualizacion en cada UPDATE.
-- Aunque el backend también la actualiza explícitamente, este trigger
-- garantiza consistencia si se modifica la fila desde SQL directo.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_visitantes_actualizacion ON visitantes;

CREATE TRIGGER trg_visitantes_actualizacion
    BEFORE UPDATE ON visitantes
    FOR EACH ROW
    EXECUTE FUNCTION set_fecha_actualizacion();
