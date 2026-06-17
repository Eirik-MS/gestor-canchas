# Gestor de Canchas de Fútbol ⚽
Proyecto Final — Estructura de Datos y Programación  
ITBA — Junio 2026  
**Equipo 3:** Martina Mattias Raposo, Eirik Mathias Silnes, Federico Nicolás Aravena Manuelides, Luciano del Valle Calvo, Valentina Iribarren, Facundo López Sierra, Juliana Malvicini, Agustina Mathieu

---

## ¿Qué es esta aplicación?
Sistema de gestión de reservas de canchas de fútbol multi-complejo.
Permite a jugadores buscar y reservar canchas en distintos complejos deportivos,
y a los complejos gestionar sus canchas y reservas.

---

## Cómo correr el proyecto

### 1. Clonar el repositorio
```bash
git clone <url-del-repo>
cd gestor-canchas
```

### 2. Crear el entorno virtual e instalar dependencias
```bash
python3 -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 3. Configurar la base de datos
- Tener MySQL instalado y corriendo
- Abrir MySQL Workbench
- Abrir el archivo `canchas_bd.sql` y ejecutarlo (⚡)

### 4. Configurar las credenciales
Crear un archivo `.env` en la raíz del proyecto:
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=tu_password ponganle la que quieran
DB_NAME=canchas_db
```

### 5. Correr la aplicación

#### Console:

```bash
cd backend
python3 main.py
```

#### Interfaze web (Flask):
Ejecuta la aplicación mediante navegador web.
```
python3 webserver.py
```
Abrir en el navegador: [http://localhost:8080](http://localhost:8080)
En modo desarrollo Flask recarga automáticamente los cambios realizados en los archivos Python.
---

## Usuario de prueba
Para probar el sistema sin registrarse:

| Campo    | Valor                  |
|----------|------------------------|
| Email    | martinam@gmail.com      |
| Password | hola123                 |
| DNI      | 99999999                |

---

## Complejos de prueba
Para probar el login de complejo:

| Complejo                    | Email                  | Password |
|-----------------------------|------------------------|----------|
| Club Atlético San Martín    | sanmartin@club.com     | (ver BD) |
| Complejo La Cancha          | lacancha@mail.com      | (ver BD) |
| Sports Center Norte         | sports@norte.com       | (ver BD) |

> Los complejos de prueba tienen passwords hasheadas en el SQL de ejemplo.
> Para probar el login de complejo, registrá uno nuevo desde el menú.

---

## Estructura del proyecto
```
gestor-canchas/
├── .env                            ← credenciales locales (NO se sube a GitHub)
├── .env.example                    ← plantilla de credenciales
├── .gitignore
├── requirements.txt                ← dependencias Python
├── canchas_bd.sql                  ← script SQL para crear la BD
├── backend/
|   ├── conexion.py                 ← conexión a MySQL
|   ├── main.py                     ← punto de entrada / menú principal
|   └── models/
|       ├── __init__.py
|       ├── usuarios.py             ← ABMC de usuarios + login
|       ├── complejos.py            ← ABMC de complejos + login
|       ├── canchas.py              ← ABMC de canchas + búsqueda disponible
|       └── reservas.py             ← crear reservas, lista de espera
├── frontend/                       ← carpeta para páginas web
│   ├── base.html 
│   └── index.html
├── static/                         ← carpeta para archivos estáticos que Flask puede usar
│   ├── css/ 
│   |   ├── bootstrap.min.css       ← Un framework para el diseño de sitios web
│   │   └── style.css
│   ├── js/
|   |   └── bootstrap.bundle.min.js ← Un framework para el diseño de sitios web
|   └── images/                     ← Todos a la picturas
└── webserver.py                    ← Flask webserver
```

---

## Flujo principal
```
Inicio
├── Soy jugador
│   ├── Tengo cuenta → Login → Reservar cancha / Ver mis reservas
│   └── No tengo cuenta → Registrarme → Login
└── Soy complejo
    ├── Login → Ver mis canchas
    └── Registrar nuevo complejo
```

---

## Base de datos
**12 tablas:** provincia · ciudad · barrio · complejo · horario_complejo ·
tipo_cancha · cancha · usuario · reserva · medio_pago · pago · lista_espera

**Características:**
- Passwords encriptadas con bcrypt
- Baja lógica en todas las tablas (fecha_baja)
- Validación de horarios del complejo al reservar
- Lista de espera para reservas con pago pendiente en efectivo

---

## Sprint 1 — Entregables completados
- [x] Base de datos creada con todas las tablas
- [x] ABMC de usuarios con encriptación de password
- [x] ABMC de complejos con login propio
- [x] ABMC de canchas con búsqueda por disponibilidad
- [x] Flujo completo de reserva
- [x] Historial de reservas por usuario
- [x] Conexión a MySQL con variables de entorno

## Sprint 2 — Próximas funcionalidades
- [ ] Métodos de pago (efectivo, transferencia, tarjeta)
- [ ] Panel del complejo con estado de pagos
- [ ] Lista de espera funcional
- [ ] Interfaz gráfica (Flask)
