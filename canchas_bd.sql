-- ============================================================
-- BASE DE DATOS: Gestor de Reservas - Canchas de Fútbol
-- v4 — con barrio, filtro de búsqueda y lista de espera
-- Proyecto Final - Estructura de Datos y Programación
-- ITBA - Junio 2026
-- ============================================================
-- FLUJO LISTA DE ESPERA:
--   1. Usuario A reserva con efectivo → pago.estado = 'pendiente'
--                                     → pago.fecha_limite_pago = fecha+hora_inicio - 40 min
--   2. Usuario B ve el turno como "reservado/pendiente de pago"
--      y puede anotarse en lista_espera
--   3. Si a los 40 min antes del turno el pago sigue pendiente,
--      el complejo ve la alerta en su panel y transfiere el turno
--      manualmente al usuario en espera
--   4. Al transferir: reserva original → cancelada,
--                     nueva reserva para usuario B,
--                     lista_espera.estado → 'asignado'
-- ============================================================

CREATE DATABASE IF NOT EXISTS canchas_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE canchas_db;

-- ============================================================
-- TABLA: provincia
-- ============================================================
CREATE TABLE IF NOT EXISTS provincia (
    id_provincia    INT          NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_provincia PRIMARY KEY (id_provincia)
);

-- ============================================================
-- TABLA: ciudad
-- ============================================================
CREATE TABLE IF NOT EXISTS ciudad (
    id_ciudad       INT          NOT NULL AUTO_INCREMENT,
    id_provincia    INT          NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_ciudad PRIMARY KEY (id_ciudad),
    CONSTRAINT fk_ciudad_provincia
        FOREIGN KEY (id_provincia) REFERENCES provincia(id_provincia)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: barrio
-- Nuevo nivel de segmentación geográfica entre ciudad y complejo.
-- Permite al usuario filtrar "canchas en Palermo", etc.
-- ============================================================
CREATE TABLE IF NOT EXISTS barrio (
    id_barrio       INT          NOT NULL AUTO_INCREMENT,
    id_ciudad       INT          NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_barrio PRIMARY KEY (id_barrio),
    CONSTRAINT fk_barrio_ciudad
        FOREIGN KEY (id_ciudad) REFERENCES ciudad(id_ciudad)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: tipo_cancha
-- Catálogo: Fútbol 5 / 7 / 11 con su estándar de capacidad.
-- ============================================================
CREATE TABLE IF NOT EXISTS tipo_cancha (
    id_tipo_cancha      INT          NOT NULL AUTO_INCREMENT,
    nombre              VARCHAR(50)  NOT NULL UNIQUE,
    capacidad_jugadores INT          NOT NULL,
    descripcion         VARCHAR(255),
    fecha_alta          DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja          DATETIME     DEFAULT NULL,
    CONSTRAINT pk_tipo_cancha PRIMARY KEY (id_tipo_cancha)
);

-- ============================================================
-- TABLA: medio_pago
-- Catálogo: Efectivo / Transferencia / Tarjeta.
-- ============================================================
CREATE TABLE IF NOT EXISTS medio_pago (
    id_medio_pago   INT          NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255),
    activo          BOOLEAN      DEFAULT TRUE,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_medio_pago PRIMARY KEY (id_medio_pago)
);

-- ============================================================
-- TABLA: complejo
-- Ahora referencia id_barrio en lugar de id_ciudad directamente.
-- ============================================================
CREATE TABLE IF NOT EXISTS complejo (
    id_complejo     INT          NOT NULL AUTO_INCREMENT,
    id_barrio       INT          NOT NULL,
    nombre          VARCHAR(100) NOT NULL,
    direccion       VARCHAR(150) NOT NULL,
    telefono        VARCHAR(20),
    email           VARCHAR(100) NOT NULL UNIQUE,
    password        VARCHAR(255) NOT NULL,
    descripcion     VARCHAR(255),
    activo          BOOLEAN      DEFAULT TRUE,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_complejo PRIMARY KEY (id_complejo),
    CONSTRAINT fk_complejo_barrio
        FOREIGN KEY (id_barrio) REFERENCES barrio(id_barrio)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: horario_complejo
-- dia_semana: 1=Lunes … 7=Domingo (usar isoweekday() en Python)
-- ============================================================
CREATE TABLE IF NOT EXISTS horario_complejo (
    id_horario      INT      NOT NULL AUTO_INCREMENT,
    id_complejo     INT      NOT NULL,
    dia_semana      TINYINT  NOT NULL,
    hora_apertura   TIME     NOT NULL,
    hora_cierre     TIME     NOT NULL,
    activo          BOOLEAN  DEFAULT TRUE,
    fecha_alta      DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME DEFAULT NULL,
    CONSTRAINT pk_horario     PRIMARY KEY (id_horario),
    CONSTRAINT fk_horario_complejo
        FOREIGN KEY (id_complejo) REFERENCES complejo(id_complejo)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT uq_complejo_dia   UNIQUE (id_complejo, dia_semana),
    CONSTRAINT chk_dia_semana    CHECK  (dia_semana BETWEEN 1 AND 7),
    CONSTRAINT chk_horario_ok    CHECK  (hora_cierre > hora_apertura OR hora_cierre <= '03:00:00')
);

-- ============================================================
-- TABLA: cancha
-- ============================================================
CREATE TABLE IF NOT EXISTS cancha (
    id_cancha           INT             NOT NULL AUTO_INCREMENT,
    id_complejo         INT             NOT NULL,
    id_tipo_cancha      INT             NOT NULL,
    nombre              VARCHAR(50)     NOT NULL,
    techada             BOOLEAN         DEFAULT FALSE,
    precio_por_hora     DECIMAL(10,2)   NOT NULL,
    disponible          BOOLEAN         DEFAULT TRUE,
    fecha_alta          DATETIME        DEFAULT CURRENT_TIMESTAMP,
    fecha_baja          DATETIME        DEFAULT NULL,
    CONSTRAINT pk_cancha PRIMARY KEY (id_cancha),
    CONSTRAINT fk_cancha_complejo
        FOREIGN KEY (id_complejo)    REFERENCES complejo(id_complejo)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_cancha_tipo
        FOREIGN KEY (id_tipo_cancha) REFERENCES tipo_cancha(id_tipo_cancha)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- TABLA: usuario
-- ============================================================
CREATE TABLE IF NOT EXISTS usuario (
    dni             INT          NOT NULL,
    nombre          VARCHAR(50)  NOT NULL,
    apellido        VARCHAR(50)  NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    telefono        VARCHAR(20),
    password        VARCHAR(255) NOT NULL,
    activo          BOOLEAN      DEFAULT TRUE,
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_usuario PRIMARY KEY (dni)
);

-- ============================================================
-- TABLA: reserva
-- estado: confirmada / cancelada / completada
-- ============================================================
CREATE TABLE IF NOT EXISTS reserva (
    id_reserva      INT             NOT NULL AUTO_INCREMENT,
    dni             INT             NOT NULL,
    id_cancha       INT             NOT NULL,
    fecha           DATE            NOT NULL,
    hora_inicio     TIME            NOT NULL,
    hora_fin        TIME            NOT NULL,
    total           DECIMAL(10,2)   NOT NULL,
    estado          VARCHAR(20)     DEFAULT 'confirmada',
    fecha_alta      DATETIME        DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME        DEFAULT NULL,
    CONSTRAINT pk_reserva PRIMARY KEY (id_reserva),
    CONSTRAINT fk_reserva_usuario
        FOREIGN KEY (dni)       REFERENCES usuario(dni)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_reserva_cancha
        FOREIGN KEY (id_cancha) REFERENCES cancha(id_cancha)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT uq_cancha_fecha_horario
        UNIQUE (id_cancha, fecha, hora_inicio),
    CONSTRAINT chk_estado_reserva
        CHECK (estado IN ('confirmada','cancelada','completada'))
);

-- ============================================================
-- TABLA: pago
-- fecha_limite_pago: calculada en Python como
--   DATETIME(fecha, hora_inicio) - INTERVAL 40 MINUTE
-- Solo aplica cuando id_medio_pago = efectivo o transferencia.
-- Para tarjeta nace como 'pagado' y sin fecha_limite.
-- ============================================================
CREATE TABLE IF NOT EXISTS pago (
    id_pago             INT             NOT NULL AUTO_INCREMENT,
    id_reserva          INT             NOT NULL UNIQUE,
    id_medio_pago       INT             NOT NULL,
    nro_operacion       VARCHAR(100)    DEFAULT NULL,
    monto               DECIMAL(10,2)   NOT NULL,
    fecha_pago          DATETIME        DEFAULT CURRENT_TIMESTAMP,
    estado_pago         VARCHAR(20)     NOT NULL DEFAULT 'pendiente',
    fecha_limite_pago   DATETIME        DEFAULT NULL,
    observaciones       VARCHAR(255)    DEFAULT NULL,
    fecha_alta          DATETIME        DEFAULT CURRENT_TIMESTAMP,
    fecha_baja          DATETIME        DEFAULT NULL,
    CONSTRAINT pk_pago PRIMARY KEY (id_pago),
    CONSTRAINT fk_pago_reserva
        FOREIGN KEY (id_reserva)    REFERENCES reserva(id_reserva)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_pago_medio
        FOREIGN KEY (id_medio_pago) REFERENCES medio_pago(id_medio_pago)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_estado_pago
        CHECK (estado_pago IN ('pendiente','pagado','devuelto'))
);

-- ============================================================
-- TABLA: lista_espera
-- Un solo usuario en espera por reserva (UNIQUE en id_reserva).
-- estado: esperando / asignado / expirado / cancelado
--   esperando → el usuario sigue en espera
--   asignado  → el complejo le transfirió el turno
--   expirado  → el dueño original pagó a tiempo, no hubo transferencia
--   cancelado → el usuario en espera desistió
-- ============================================================
CREATE TABLE IF NOT EXISTS lista_espera (
    id_espera       INT          NOT NULL AUTO_INCREMENT,
    id_reserva      INT          NOT NULL UNIQUE,   -- la reserva que está pendiente de pago
    dni             INT          NOT NULL,           -- usuario que quiere ese turno
    fecha_anotado   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    estado          VARCHAR(20)  DEFAULT 'esperando',
    fecha_alta      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME     DEFAULT NULL,
    CONSTRAINT pk_espera PRIMARY KEY (id_espera),
    CONSTRAINT fk_espera_reserva
        FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_espera_usuario
        FOREIGN KEY (dni) REFERENCES usuario(dni)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_estado_espera
        CHECK (estado IN ('esperando','asignado','expirado','cancelado'))
);

-- ============================================================
-- DATOS DE PRUEBA
-- ============================================================

INSERT INTO provincia (nombre) VALUES
('Buenos Aires'),('Córdoba'),('Santa Fe'),('Mendoza');

INSERT INTO ciudad (id_provincia, nombre) VALUES
(1,'CABA'),(1,'La Plata'),(1,'Mar del Plata'),(1,'Ramos Mejía'),(2,'Córdoba'),(3,'Rosario');

INSERT INTO barrio (id_ciudad, nombre) VALUES
(1,'Palermo'),(1,'Belgrano'),(1,'Almagro'),(1,'Villa Urquiza'),
(1,'Caballito'),(1,'Flores'),(4,'Centro'),(4,'Villa del Parque');

INSERT INTO tipo_cancha (nombre, capacidad_jugadores, descripcion) VALUES
('Fútbol 5',  10, '5 jugadores por equipo. Cancha pequeña con paredes o alambrado'),
('Fútbol 7',  14, '7 jugadores por equipo. Cancha mediana sin paredes'),
('Fútbol 11', 22, '11 jugadores por equipo. Cancha reglamentaria');

INSERT INTO medio_pago (nombre, descripcion) VALUES
('Efectivo',      'Pago en el complejo. Genera lista de espera si no paga a tiempo'),
('Transferencia', 'Transferencia bancaria. Requiere número de comprobante'),
('Tarjeta',       'Débito o crédito. Se acredita de forma inmediata');

INSERT INTO complejo (id_barrio, nombre, direccion, telefono, email, password, descripcion) VALUES
(1,'Club Atlético San Martín','Av. Santa Fe 3400',  '1144441111','sanmartin@club.com','$2b$12$HASH_C1','Canchas techadas, vestuarios y bar'),
(3,'Complejo La Cancha',      'Calle Medrano 1200', '1144442222','lacancha@mail.com', '$2b$12$HASH_C2','Fútbol 5, 7 y 11. Estacionamiento gratis'),
(2,'Sports Center Norte',     'Av. Cabildo 5600',   '1144443333','sports@norte.com',  '$2b$12$HASH_C3','Canchas premium con iluminación LED');

INSERT INTO horario_complejo (id_complejo, dia_semana, hora_apertura, hora_cierre) VALUES
(1,1,'08:00','00:00'),(1,2,'08:00','00:00'),(1,3,'08:00','00:00'),
(1,4,'08:00','00:00'),(1,5,'08:00','00:00'),(1,6,'09:00','23:00'),(1,7,'09:00','23:00'),
(2,1,'09:00','23:00'),(2,2,'09:00','23:00'),(2,3,'09:00','23:00'),
(2,4,'09:00','23:00'),(2,5,'09:00','23:00'),(2,6,'09:00','23:00'),(2,7,'09:00','22:00'),
(3,1,'08:00','01:00'),(3,2,'08:00','01:00'),(3,3,'08:00','01:00'),
(3,4,'08:00','01:00'),(3,5,'08:00','01:00'),(3,6,'08:00','01:00'),(3,7,'10:00','23:00');

INSERT INTO cancha (id_complejo, id_tipo_cancha, nombre, techada, precio_por_hora) VALUES
(1,1,'Cancha A',TRUE,9000.00),(1,1,'Cancha B',TRUE,9000.00),(1,2,'Cancha C',FALSE,12000.00),
(2,1,'Cancha 1',TRUE,8500.00),(2,2,'Cancha 2',FALSE,11500.00),(2,3,'Cancha 3',FALSE,16000.00),
(3,1,'Cancha Norte 1',TRUE,10000.00),(3,1,'Cancha Norte 2',TRUE,10000.00);

INSERT INTO usuario (dni, nombre, apellido, email, telefono, password) VALUES
(12345678,'Lucas',  'Fernández','lucas@mail.com','1155551111','$2b$12$HASH_U1'),
(23456789,'Sofía',  'Ramírez',  'sofia@mail.com','1155552222','$2b$12$HASH_U2'),
(34567890,'Nicolás','Torres',   'nico@mail.com', '1155553333','$2b$12$HASH_U3');

-- Reserva 1: Lucas reserva con efectivo → queda pendiente, Sofía se anota en espera
-- Reserva 2: Sofía reserva con transferencia → pendiente
-- Reserva 3: Nico reserva con tarjeta → pagado
-- Reserva 4: Lucas reserva completada
INSERT INTO reserva (dni, id_cancha, fecha, hora_inicio, hora_fin, total, estado) VALUES
(12345678, 1, '2026-06-10', '18:00', '19:00',  9000.00, 'confirmada'),
(23456789, 4, '2026-06-10', '20:00', '21:00',  8500.00, 'confirmada'),
(34567890, 3, '2026-06-11', '09:00', '10:30', 18000.00, 'confirmada'),
(12345678, 7, '2026-06-12', '17:00', '18:00', 10000.00, 'completada');

-- fecha_limite_pago = DATETIME(fecha, hora_inicio) - 40 minutos (calculado en Python al insertar)
INSERT INTO pago (id_reserva, id_medio_pago, nro_operacion, monto, estado_pago, fecha_limite_pago, observaciones) VALUES
(1, 1, NULL,            9000.00, 'pendiente', '2026-06-10 17:20:00', NULL),
(2, 2, 'TRF-00123456',  8500.00, 'pendiente', '2026-06-10 19:20:00', 'Alias: LACANCHA.MP'),
(3, 3, 'CUP-00789012', 18000.00, 'pagado',    NULL,                  NULL),
(4, 1, NULL,           10000.00, 'pagado',    NULL,                  'Cobrado presencialmente');

-- Sofía se anota en lista de espera para la reserva de Lucas (id_reserva=1)
INSERT INTO lista_espera (id_reserva, dni) VALUES (1, 23456789);

-- ============================================================
-- VISTAS
-- ============================================================

-- Búsqueda de canchas disponibles con filtro por provincia/ciudad/barrio/fecha/horario
-- (la consulta F más abajo la usa con parámetros)
CREATE OR REPLACE VIEW vista_busqueda_canchas AS
SELECT
    pr.id_provincia,  pr.nombre  AS provincia,
    ci.id_ciudad,     ci.nombre  AS ciudad,
    b.id_barrio,      b.nombre   AS barrio,
    co.id_complejo,   co.nombre  AS complejo,
    co.direccion,     co.telefono,
    c.id_cancha,      c.nombre   AS cancha,
    tc.nombre         AS tipo_cancha,
    tc.capacidad_jugadores,
    c.techada,
    c.precio_por_hora,
    c.disponible
FROM cancha      c
JOIN complejo    co ON c.id_complejo    = co.id_complejo
JOIN barrio      b  ON co.id_barrio     = b.id_barrio
JOIN ciudad      ci ON b.id_ciudad      = ci.id_ciudad
JOIN provincia   pr ON ci.id_provincia  = pr.id_provincia
JOIN tipo_cancha tc ON c.id_tipo_cancha = tc.id_tipo_cancha
WHERE co.activo = TRUE AND c.disponible = TRUE;

-- Panel del complejo: reservas con estado de pago y alerta de vencimiento
CREATE OR REPLACE VIEW vista_panel_complejo AS
SELECT
    co.id_complejo,
    c.id_cancha,
    c.nombre                        AS cancha,
    tc.nombre                       AS tipo_cancha,
    r.id_reserva,
    CONCAT(u.nombre,' ',u.apellido) AS usuario,
    u.telefono,
    r.fecha,
    r.hora_inicio,
    r.hora_fin,
    r.total,
    r.estado                        AS estado_reserva,
    mp.nombre                       AS medio_pago,
    p.nro_operacion,
    p.monto,
    p.estado_pago,
    p.fecha_limite_pago,
    -- Alerta visible en el panel cuando el plazo venció y sigue pendiente
    CASE
        WHEN p.estado_pago = 'pendiente'
         AND p.fecha_limite_pago IS NOT NULL
         AND NOW() >= p.fecha_limite_pago
        THEN TRUE ELSE FALSE
    END                             AS alerta_vencido,
    -- Indica si hay alguien en lista de espera para esta reserva
    CASE WHEN le.id_espera IS NOT NULL THEN TRUE ELSE FALSE
    END                             AS tiene_espera,
    le.dni                          AS dni_en_espera
FROM reserva r
JOIN cancha       c  ON r.id_cancha      = c.id_cancha
JOIN complejo     co ON c.id_complejo    = co.id_complejo
JOIN tipo_cancha  tc ON c.id_tipo_cancha = tc.id_tipo_cancha
JOIN usuario      u  ON r.dni            = u.dni
LEFT JOIN pago    p  ON r.id_reserva     = p.id_reserva
LEFT JOIN medio_pago mp ON p.id_medio_pago = mp.id_medio_pago
LEFT JOIN lista_espera le ON r.id_reserva = le.id_reserva AND le.estado = 'esperando';

-- ============================================================
-- CONSULTAS CLAVE PARA EL BACKEND PYTHON
-- ============================================================

-- A. Login complejo
-- SELECT id_complejo, nombre, password FROM complejo WHERE email = %s AND activo = TRUE;

-- B. Login usuario
-- SELECT dni, nombre, apellido, password FROM usuario WHERE email = %s AND activo = TRUE;

-- C. Provincias para el selector inicial
-- SELECT id_provincia, nombre FROM provincia WHERE fecha_baja IS NULL ORDER BY nombre;

-- D. Ciudades de una provincia
-- SELECT id_ciudad, nombre FROM ciudad WHERE id_provincia = %s AND fecha_baja IS NULL;

-- E. Barrios de una ciudad
-- SELECT id_barrio, nombre FROM barrio WHERE id_ciudad = %s AND fecha_baja IS NULL;

-- F. BÚSQUEDA PRINCIPAL: canchas disponibles filtrando por barrio + fecha + rango horario
--    Valida también que el horario esté dentro del horario del complejo ese día.
--    dia_iso: fecha.isoweekday() en Python (1=Lunes...7=Domingo)
-- SELECT v.*
-- FROM vista_busqueda_canchas v
-- WHERE v.id_barrio = %s              -- o id_ciudad si no filtra por barrio
--   AND v.id_cancha NOT IN (
--       SELECT id_cancha FROM reserva
--       WHERE fecha = %s
--         AND estado != 'cancelada'
--         AND hora_inicio < %s        -- hora_fin pedida
--         AND hora_fin    > %s        -- hora_inicio pedida
--   )
--   AND EXISTS (
--       SELECT 1 FROM horario_complejo h
--       WHERE h.id_complejo  = v.id_complejo
--         AND h.dia_semana   = %s     -- dia_iso
--         AND h.activo       = TRUE
--         AND %s >= h.hora_apertura   -- hora_inicio pedida
--         AND %s <= h.hora_cierre     -- hora_fin pedida
--   );

-- G. Calcular fecha_limite_pago en Python antes de insertar el pago:
--    from datetime import datetime, timedelta
--    dt_inicio = datetime.combine(fecha_reserva, hora_inicio)
--    fecha_limite = dt_inicio - timedelta(minutes=40)

-- H. Anotarse en lista de espera
-- INSERT INTO lista_espera (id_reserva, dni) VALUES (%s, %s);

-- I. Transferir turno (lo ejecuta el complejo desde su panel):
--    Paso 1: cancelar reserva original
--    UPDATE reserva SET estado = 'cancelada', fecha_baja = NOW() WHERE id_reserva = %s;
--    Paso 2: crear nueva reserva para el usuario en espera (misma cancha/fecha/horario)
--    INSERT INTO reserva (dni, id_cancha, fecha, hora_inicio, hora_fin, total) VALUES (%s,%s,%s,%s,%s,%s);
--    Paso 3: crear pago pendiente para la nueva reserva
--    INSERT INTO pago (id_reserva, id_medio_pago, monto, fecha_limite_pago) VALUES (%s,%s,%s,%s);
--    Paso 4: marcar lista de espera como asignada
--    UPDATE lista_espera SET estado = 'asignado' WHERE id_reserva = %s;

-- J. Reporte contable completo
-- SELECT p.id_pago, p.nro_operacion, mp.nombre AS medio, p.monto, p.estado_pago,
--        p.fecha_pago, p.observaciones, r.fecha AS fecha_reserva,
--        co.nombre AS complejo, CONCAT(u.nombre,' ',u.apellido) AS usuario
-- FROM pago p
-- JOIN medio_pago  mp ON p.id_medio_pago = mp.id_medio_pago
-- JOIN reserva     r  ON p.id_reserva    = r.id_reserva
-- JOIN cancha      c  ON r.id_cancha     = c.id_cancha
-- JOIN complejo    co ON c.id_complejo   = co.id_complejo
-- JOIN usuario     u  ON r.dni           = u.dni
-- ORDER BY p.fecha_pago DESC;

-- ============================================================
-- VERIFICACIÓN RÁPIDA
-- ============================================================
SELECT 'Tablas:' AS '';           SHOW TABLES;
SELECT 'Provincias:' AS '';       SELECT * FROM provincia;
SELECT 'Barrios:' AS '';          SELECT id_barrio, id_ciudad, nombre FROM barrio;
SELECT 'Tipos de cancha:' AS '';  SELECT * FROM tipo_cancha;
SELECT 'Medios de pago:' AS '';   SELECT * FROM medio_pago;
SELECT 'Complejos:' AS '';        SELECT id_complejo, nombre, id_barrio, activo FROM complejo;
SELECT 'Canchas:' AS '';          SELECT id_cancha, id_complejo, id_tipo_cancha, nombre, precio_por_hora FROM cancha;
SELECT 'Reservas:' AS '';         SELECT id_reserva, dni, id_cancha, fecha, hora_inicio, hora_fin, estado FROM reserva;
SELECT 'Pagos:' AS '';            SELECT id_pago, id_reserva, id_medio_pago, monto, estado_pago, fecha_limite_pago FROM pago;
SELECT 'Lista de espera:' AS '';  SELECT * FROM lista_espera;
