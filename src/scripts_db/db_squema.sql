CREATE DATABASE IF NOT EXISTS control_acceso;
USE control_acceso;

-- Tabla de roles
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL,
    nivel_acceso VARCHAR(50) NOT NULL
);

-- Tabla de usuarios
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
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
    resultado ENUM('autorizado', 'rechazado', 'error_sistema') NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Datos iniciales de prueba
INSERT INTO roles (nombre_rol, nivel_acceso) VALUES
    ('administrador', 'total'),
    ('usuario_estandar', 'limitado');

INSERT INTO usuarios (nombre, clave_acceso, id_rol) VALUES
    ('Usuario Prueba', '123123', 2);