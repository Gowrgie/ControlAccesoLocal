-- db_squema.sql

-- Base de datos MySQL del sistema. RF-11
-- utf8mb4 para que se guarden bien los acentos ("Servicio técnico")
CREATE DATABASE IF NOT EXISTS control_acceso CHARACTER SET utf8mb4;
USE control_acceso;

-- Tabla de roles con permisos diferenciables. RF-12
CREATE TABLE roles (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL,       -- nombre del rol, igual al de la interfaz
    nivel_acceso VARCHAR(50) NOT NULL,     -- nivel de acceso del rol. RF-12
    permiso_apertura BOOLEAN NOT NULL DEFAULT TRUE,          -- si puede abrir el acceso. RF-13, RF-17
    permiso_administracion BOOLEAN NOT NULL DEFAULT FALSE    -- si puede administrar usuarios. RNF-02
);

-- Tabla de usuarios identificables. RF-12
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    identificador VARCHAR(20) NOT NULL UNIQUE,   -- se captura primero, sin repetirse. RF-02
    clave_acceso VARCHAR(20) NOT NULL,           -- misma clave para botones e interfaz. RF-02, RF-14
    id_rol INT NOT NULL,                         -- rol asignado. RF-12
    FOREIGN KEY (id_rol) REFERENCES roles(id_rol)
);

-- Registro de cada intento de acceso. RF-11
CREATE TABLE intentos_acceso (
    id_intento INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,                                     -- NULL si no se reconoce al usuario o falla el sistema. RF-13
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- fecha y hora del intento. RF-11
    mecanismo ENUM('interfaz_grafica', 'botones') NOT NULL,  -- por donde se intento. RF-11, RF-14, RF-15
    resultado ENUM('autorizado', 'sin_permiso', 'no_reconocido', 'error_sistema') NOT NULL,  -- los 4 casos. RF-11, RF-13
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- Roles iniciales (nombres iguales a los de la interfaz). RF-12
INSERT INTO roles (nombre_rol, nivel_acceso, permiso_apertura, permiso_administracion) VALUES
    ('Usuario general', 'limitado', TRUE, FALSE),
    ('Administrador', 'total', TRUE, TRUE),
    ('Servicio técnico', 'tecnico', TRUE, FALSE),
    ('Sin permisos', 'sin_apertura', FALSE, FALSE);   -- solo para probar "autorizado pero sin permiso". RF-13

-- Usuarios de prueba (identificador y clave solo con digitos 1, 2 y 3, por los 3 botones). RF-02
INSERT INTO usuarios (nombre, identificador, clave_acceso, id_rol) VALUES
    ('Usuario General Prueba', '1111', '123123', 1),
    ('Administrador Prueba', '1112', '112233', 2),
    ('Servicio Técnico Prueba', '1113', '332211', 3),
    ('Usuario Sin Permisos', '1121', '321321', 4);    -- prueba de acceso restringido. RF-13

-- Usuario de MySQL que usa el programa (DB_USER en db_conexion.py)
-- Permisos minimos: solo lee usuarios/roles y solo inserta intentos. RNF-02, RNF-09
CREATE USER IF NOT EXISTS 'control_acceso'@'localhost' IDENTIFIED BY 'cambia_esta_password';
GRANT SELECT ON control_acceso.usuarios TO 'control_acceso'@'localhost';
GRANT SELECT ON control_acceso.roles TO 'control_acceso'@'localhost';
GRANT INSERT ON control_acceso.intentos_acceso TO 'control_acceso'@'localhost';  -- sin UPDATE/DELETE: los registros no se alteran. RNF-09
FLUSH PRIVILEGES;