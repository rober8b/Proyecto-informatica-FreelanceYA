from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import requests
import csv


app = Flask(__name__)


class Usuario:
    def __init__(self, id, nombre, email, rol):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.rol = rol

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'rol': self.rol
        }


class Servicio:
    def __init__(self, id, titulo, descripcion, precio, freelancer_id):
        self.id = id
        self.titulo = titulo
        self.descripcion = descripcion
        self.precio = precio
        self.freelancer_id = freelancer_id

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descripcion': self.descripcion,
            'precio': self.precio,
            'freelancer': self.freelancer_id
        }


class Order:
    def __init__(self, id, nombre_servicio, nombre_usuario, nombre_freelancer, descripcion, precio):
        self.id = id
        self.nombre_servicio = nombre_servicio
        self.nombre_usuario = nombre_usuario
        self.nombre_freelancer = nombre_freelancer
        self.descripcion = descripcion
        self.precio = precio

    def to_dict(self):
        return {
            'id': self.id,
            'nombre_servicio': self.nombre_servicio,
            'nombre_usuario': self.nombre_usuario,
            'nombre_freelancer': self.nombre_freelancer,
            'descripcion': self.descripcion,
            'precio': self.precio
        }


def crear_tablas():
    with sqlite3.connect("servicios.db") as conexion:
        cursor = conexion.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                email TEXT UNIQUE,
                password TEXT,
                rol TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                descripcion TEXT,
                precio REAL,
                freelancer_id INTEGER,
                FOREIGN KEY(freelancer_id) REFERENCES usuarios(id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_servicio TEXT,
                nombre_usuario TEXT,
                nombre_freelancer TEXT,
                descripcion TEXT,
                precio REAL
            )
        ''')
crear_tablas()


def conectar_db():
    return sqlite3.connect("servicios.db")


def exportar_ordenes_a_csv(nombre_archivo='ordenes.csv'):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        filas = cursor.fetchall()

    with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as archivo_csv:
        escritor = csv.writer(archivo_csv)
        escritor.writerow(['id', 'nombre_servicio', 'nombre_usuario', 'nombre_freelancer', 'descripcion', 'precio'])
        escritor.writerows(filas)

    print(f"Archivo {nombre_archivo} generado con éxito.")

# ------------------ ENDPOINTS REGISTRO/LOGIN------------------
@app.route('/registro', methods=['POST'])
def registro():
    data = request.get_json()
    nombre = data['nombre']
    email = data['email']
    password = data['password']
    rol = data['rol']

    password_hash = generate_password_hash(password)

    with conectar_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?)",
                           (nombre, email, password_hash, rol))
            conn.commit()
            return jsonify({'mensaje': 'Usuario registrado correctamente'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'El email ya está registrado'}), 400
        
        
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, password, rol FROM usuarios WHERE email=?", (email,))
        fila = cursor.fetchone()

        if fila and check_password_hash(fila[2], password):
            return jsonify({'mensaje': 'Login exitoso', 'usuario': {
                'id': fila[0], 'nombre': fila[1], 'email': email, 'rol': fila[3]
            }})
        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        

# ------------------ ENDPOINTS USUARIOS ------------------
@app.route('/usuarios', methods=['POST'])
def crear_usuario():
    data = request.get_json()
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email, rol) VALUES (?, ?, ?)",
                       (data['nombre'], data['email'], data['rol']))
        conn.commit()
    return jsonify({'mensaje': 'Usuario creado'}), 201


@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios")
        filas = cursor.fetchall()
        usuarios = [{'id': f[0], 'nombre': f[1], 'email': f[2], 'rol': f[3]} for f in filas]
    return jsonify(usuarios)


# ------------------ ENDPOINTS SERVICIOS ------------------
@app.route('/servicios', methods=['POST'])
def crear_servicio():
    data = request.get_json()
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO servicios (titulo, descripcion, precio, freelancer_id) VALUES (?, ?, ?, ?)",
                       (data['titulo'], data['descripcion'], data['precio'], data['freelancer_id']))
        conn.commit()
    return jsonify({'mensaje': 'Servicio creado'}), 201


@app.route('/servicios', methods=['GET'])
def listar_servicios():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios")
        filas = cursor.fetchall()
        servicios = [{'id': f[0], 'titulo': f[1], 'descripcion': f[2], 'precio': f[3], 'freelancer': f[4]} for f in filas]
    return jsonify(servicios)


# ------------------ API PROPIA: BUSQUEDA POR PALABRA CLAVE ------------------
@app.route('/servicios/buscar', methods=['GET'])
def buscar_servicios():
    palabra = request.args.get('q', '').lower()

    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM servicios")
        filas = cursor.fetchall()
        servicios = []

        for f in filas:
            if palabra in f[1].lower() or palabra in f[2].lower():
                servicios.append({
                    'id': f[0],
                    'titulo': f[1],
                    'descripcion': f[2],
                    'precio': f[3],
                    'freelancer': f[4]
                })

    return jsonify(servicios)


@app.route('/servicios/<int:id>', methods=['PUT'])
def actualizar_servicio(id):
    data = request.get_json()
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE servicios SET titulo=?, descripcion=?, precio=?, freelancer_id=? WHERE id=?",
                       (data['titulo'], data['descripcion'], data['precio'], data['freelancer_id'], id))
        conn.commit()
    return jsonify({'mensaje': 'Servicio actualizado'})


@app.route('/servicios/<int:id>', methods=['DELETE'])
def eliminar_servicio(id):
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM servicios WHERE id=?", (id,))
        conn.commit()
    return jsonify({'mensaje': 'Servicio eliminado'})


# ------------------ ENDPOINTS ORDENES ------------------
@app.route('/ordenes', methods=['POST'])
def crear_orden():
    data = request.get_json()
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO orders (nombre_servicio, nombre_usuario, nombre_freelancer, descripcion, precio) VALUES (?, ?, ?, ?, ?)",
                       (data['nombre_servicio'], data['nombre_usuario'], data['nombre_freelancer'], data['descripcion'], data['precio']))
        conn.commit()
    return jsonify({'mensaje': 'Orden creada'}), 201


@app.route('/ordenes', methods=['GET'])
def listar_ordenes():
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders")
        filas = cursor.fetchall()
        ordenes = [{'id': f[0], 'nombre_servicio': f[1], 'nombre_usuario': f[2], 'nombre_freelancer': f[3], 'descripcion': f[4], 'precio': f[5]} for f in filas]
    return jsonify(ordenes)

@app.route('/exportar_ordenes', methods=['GET'])
def exportar_ordenes():
    exportar_ordenes_a_csv()
    return jsonify({'mensaje': 'Archivo CSV de órdenes generado'})

# ------------------ API DE TERCEROS: CONVERSOR MONEDAS ------------------
@app.route('/convertir_multiples', methods=['GET'])
def convertir_multiples_monedas():
    try:
        monto = float(request.args.get('monto', 1))
    except ValueError:
        return jsonify({'error': 'Monto inválido'}), 400
    monedas_destino = request.args.get('monedas_destino', 'EUR,ARS').upper().split(',')

    API_KEY = '4bb0171cf77f6601a51d2a59'
    url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD'

    try:
        response = requests.get(url)
        data = response.json()
        conversiones = {}

        for moneda in monedas_destino:
            tasa = data['conversion_rates'].get(moneda)
            if tasa:
                conversiones[moneda] = round(monto * tasa, 2)
            else:
                conversiones[moneda] = 'Moneda no encontrada'

        return jsonify({
            'monto_usd': monto,
            'conversiones': conversiones
        })

    except Exception as e:
        return jsonify({'error': 'No se pudo acceder a la API externa', 'detalle': str(e)}), 500
    
__all__ = ['app', 'conectar_db', 'crear_tablas']

if __name__ == '__main__':
    app.run(debug=True)

# ----------------------------------------------------------------------------
# ------------------ FUNCIONES DE FRONT END PARA EL USUARIO ------------------
# ----------------------------------------------------------------------------
# def registrar_usuario_consola():
#     print("\n--- Registro de Usuario ---")
#     nombre = input("Nombre: ")
#     email = input("Email: ")
#     password = input("Contraseña: ")
#     rol = input("Rol (cliente/freelancer): ").lower()
    
#     if rol not in ['cliente', 'freelancer']:
#         print("Rol debe ser 'cliente' o 'freelancer'")
#         return
    
#     with app.test_client() as client:
#         response = client.post('/registro', json={
#             'nombre': nombre,
#             'email': email,
#             'password': password,
#             'rol': rol
#         })
        
#         data = response.get_json()
#         if response.status_code == 201:
#             print(f"Usuario registrado: {data['mensaje']}")
#         else:
#             print(f"Error: {data.get('error', 'Error desconocido')}")

# def login_usuario_consola():
#     print("\n--- Inicio de Sesión ---")
#     email = input("Email: ")
#     password = input("Contraseña: ")
    
#     with app.test_client() as client:
#         response = client.post('/login', json={
#             'email': email,
#             'password': password
#         })
        
#         data = response.get_json()
#         if response.status_code == 200:
#             print(f"Login exitoso. Bienvenido {data['usuario']['nombre']} ({data['usuario']['rol']})")
#             return data['usuario']
#         else:
#             print(f"Error: {data.get('error', 'Credenciales inválidas')}")
#             return None

# def listar_servicios_consola():
#     print("\n--- Listado de Servicios ---")
#     with app.test_client() as client:
#         response = client.get('/servicios')
#         servicios = response.get_json()
        
#         if not servicios:
#             print("No hay servicios disponibles")
#             return
        
#         for servicio in servicios:
#             print(f"\nID: {servicio['id']}")
#             print(f"Título: {servicio['titulo']}")
#             print(f"Descripción: {servicio['descripcion']}")
#             print(f"Precio: ${servicio['precio']}")
#             print(f"Freelancer ID: {servicio['freelancer']}")

# def crear_servicio_consola():
#     print("\n--- Crear Nuevo Servicio ---")
#     usuario = login_usuario_consola()
#     if not usuario or usuario['rol'] != 'freelancer':
#         print("Debes iniciar sesión como freelancer para crear servicios")
#         return
    
#     titulo = input("Título del servicio: ")
#     descripcion = input("Descripción: ")
#     precio = float(input("Precio: "))
    
#     with app.test_client() as client:
#         response = client.post('/servicios', json={
#             'titulo': titulo,
#             'descripcion': descripcion,
#             'precio': precio,
#             'freelancer_id': usuario['id']
#         })
        
#         data = response.get_json()
#         if response.status_code == 201:
#             print(f"Servicio creado: {data['mensaje']}")
#         else:
#             print(f"Error al crear servicio")

# def crear_orden_consola():
#     print("\n--- Crear Nueva Orden ---")
#     usuario = login_usuario_consola()
#     if not usuario or usuario['rol'] != 'cliente':
#         print("Debes iniciar sesión como cliente para crear órdenes")
#         return
    
#     listar_servicios_consola()
#     id_servicio = input("\nIngrese el ID del servicio que desea contratar: ")
    
#     with app.test_client() as client:
#         response = client.get('/servicios')
#         servicios = response.get_json()
#         servicio_seleccionado = next((s for s in servicios if str(s['id']) == id_servicio), None)
        
#         if not servicio_seleccionado:
#             print("ID de servicio no válido")
#             return
        
#         with conectar_db() as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT nombre FROM usuarios WHERE id=?", (servicio_seleccionado['freelancer'],))
#             nombre_freelancer = cursor.fetchone()[0]
        
#         response = client.post('/ordenes', json={
#             'nombre_servicio': servicio_seleccionado['titulo'],
#             'nombre_usuario': usuario['nombre'],
#             'nombre_freelancer': nombre_freelancer,
#             'descripcion': servicio_seleccionado['descripcion'],
#             'precio': servicio_seleccionado['precio']
#         })
        
#         data = response.get_json()
#         if response.status_code == 201:
#             print(f"Orden creada: {data['mensaje']}")
#         else:
#             print(f"Error al crear orden")


# ------------------ MENU ------------------
# def menu():
#     while True:
#         print("\n--- FreelanceYA ---")
#         print("1. Registrar usuario")
#         print("2. Iniciar sesión")
#         print("3. Listar servicios")
#         print("4. Crear servicio (Freelancer)")
#         print("5. Crear orden (Cliente)")
#         print("6. Salir")
        
#         opcion = input("Seleccione una opción: ")
        
#         if opcion == "1":
#             registrar_usuario_consola()
#         elif opcion == "2":
#             login_usuario_consola()
#         elif opcion == "3":
#             listar_servicios_consola()
#         elif opcion == "4":
#             crear_servicio_consola()
#         elif opcion == "5":
#             crear_orden_consola()
#         elif opcion == "6":
#             print("Saliendo...")
#             break
#         else:
#             print("Opción no válida")

# # ------------------ MAIN ------------------
# if __name__ == '__main__':
#     crear_tablas()
#     menu()