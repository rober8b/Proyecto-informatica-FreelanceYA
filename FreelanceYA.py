from flask import Flask, request, jsonify
import sqlite3
import requests

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
                email TEXT,
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
        cursor.execute("INSERT INTO servicios (titulo, descripcion, precio, freelancer) VALUES (?, ?, ?, ?)",
                       (data['titulo'], data['descripcion'], data['precio'], data['freelancer']))
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


@app.route('/servicios/<int:id>', methods=['PUT'])
def actualizar_servicio(id):
    data = request.get_json()
    with conectar_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE servicios SET titulo=?, descripcion=?, precio=?, freelancer=? WHERE id=?",
                       (data['titulo'], data['descripcion'], data['precio'], data['freelancer'], id))
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

# ------------------ API DE TERCEROS: CONVERSOR MONEDAS ------------------
@app.route('/convertir_multiples', methods=['GET'])
def convertir_multiples_monedas():
    monto = float(request.args.get('monto', 1))
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


# ------------------ MAIN ------------------
if __name__ == '__main__':
    app.run(debug=True)
