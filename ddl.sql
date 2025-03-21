CREATE SCHEMA dq

-- Tabla principal que almacena las tablas de datos a validar
CREATE TABLE dq.cat_origen_datos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(500) NOT NULL UNIQUE,
    descripcion VARCHAR(MAX) NULL
);

CREATE TABLE dq.cat_tipo_reglas_negocio (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(500) NOT NULL UNIQUE
);

INSERT INTO dq.cat_tipo_reglas_negocio(nombre)
VALUES
('NO_NULO'),
('UNICO'),
('EXPRESION_REGULAR'),
('MINIMO'),
('MAXIMO'),
('CANTIDAD_REGISTROS'),
('PROMEDIO'),
('DESVIACION_ESTANDAR'),
('FUNCION_PERSONALIZADA');

SELECT * FROM dq.cat_tipo_reglas_negocio ORDER BY id

-- Tabla que almacena las reglas de validación
CREATE TABLE dq.tbl_reglas_negocio (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cat_origen_datos_id INT NOT NULL REFERENCES dq.cat_origen_datos,
    nombre_columna VARCHAR(100) NOT NULL,
    cat_tipo_reglas_negocio_id INT NOT NULL REFERENCES dq.cat_tipo_reglas_negocio,  -- NO_NULO, UNICO, EXPRESION_REGULAR, MINIMO, MAXIMO, CANTIDAD_REGISTROS, PROMEDIO, DESVIACION_ESTANDAR, FUNCION_PERSONALIZADA
    valor_regla VARCHAR(MAX) NULL,
    mensaje_error VARCHAR(500) NOT NULL
);

-- Insertar una tabla de origen de datos
INSERT INTO dq.cat_origen_datos (nombre, descripcion) VALUES 
('datos_prueba', 'Tabla de datos de ejemplo para validaciones');

SELECT * FROM dq.cat_origen_datos

-- Insertar reglas de negocio para la tabla de origen
INSERT INTO dq.tbl_reglas_negocio (cat_origen_datos_id, nombre_columna, cat_tipo_reglas_negocio_id, valor_regla, mensaje_error) VALUES
(1, 'edad', 4, '18', 'La edad debe ser al menos 18 años'),
(1, 'salario', 5, '50000', 'El salario no puede exceder los 50,000'),
(1, 'email', 3, '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}$', 'El email no es válido'),
(1, 'codigo', 2, NULL, 'El código debe ser único'),
(1, 'codigo', 9, 'def validar_codigo(valor): return valor.startswith(\"A\")', 'Código no valido');


SELECT * FROM dq.tbl_reglas_negocio