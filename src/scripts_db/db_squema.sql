CREATE DATABASE IF NOT EXISTS control_acceso;
USE control_acceso;

-- Tabla de roles
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL,
    nivel_acceso VARCHAR(50) NOT NULL,
    permiso_apertura BOOLEAN NOT NULL DEFAULT TRUE,       -- puede abrir el acceso
    permiso_administracion BOOLEAN NOT NULL DEFAULT FALSE -- puede administrar usuarios/roles
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    identificador VARCHAR(20) NOT NULL UNIQUE,  -- <-- NUEVO, RF-02 pide capturar un identificador de usuario ANTES de la clave
    clave_acceso VARCHAR(20) NOT NULL,
    id_rol INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

-- Tabla de intentos de acceso
CREATE TABLE intentos_acceso (
    id_intento INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL, 
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mecanismo ENUM('interfaz_grafica', 'botones') NOT NULL,
    resultado ENUM('autorizado', 'sin_permiso', 'no_reconocido', 'error_sistema') NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Datos iniciales de prueba
INSERT INTO roles (nombre_rol, nivel_acceso, permiso_apertura, permiso_administracion) VALUES
    ('administrador', 'total', TRUE, TRUE),
    ('usuario_general', 'limitado', TRUE, FALSE),
    ('usuario_restringido', 'sin_apertura', FALSE, FALSE);  -- <-- este rol es para probar RF-13 "sin permiso"

INSERT INTO usuarios (nombre, identificador, clave_acceso, id_rol) VALUES
    ('Usuario Admin', 'A001', '123123', 1),
    ('Usuario Prueba', 'U001', '112233', 2),
    ('Usuario Sin Permiso', 'U002', '321321', 3);