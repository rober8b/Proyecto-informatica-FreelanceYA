from backend import app, conectar_db
import json

def registrar_usuario_consola():
    print("\n--- Registro de Usuario ---")
    nombre = input("Nombre: ")
    email = input("Email: ")
    password = input("Contraseña: ")
    rol = input("Rol (cliente/freelancer): ").lower()
    
    if rol not in ['cliente', 'freelancer']:
        print("Rol debe ser 'cliente' o 'freelancer'")
        return
    
    with app.test_client() as client:
        response = client.post('/registro', json={
            'nombre': nombre,
            'email': email,
            'password': password,
            'rol': rol
        })
        
        data = response.get_json()
        if response.status_code == 201:
            print(f"Usuario registrado: {data['mensaje']}")
        else:
            print(f"Error: {data.get('error', 'Error desconocido')}")

#ESTA FUNCION NO SE UTILIZA DIRECTAMENTE SINO QUE LA UTILIZAMOS A TRAVES DE LAS OTRAS
def login_usuario_consola():                    
    print("\n--- Inicio de Sesión ---")
    email = input("Email: ")
    password = input("Contraseña: ")
    
    with app.test_client() as client:
        response = client.post('/login', json={
            'email': email,
            'password': password
        })
        
        data = response.get_json()
        if response.status_code == 200:
            print(f"Login exitoso. Bienvenido {data['usuario']['nombre']} ({data['usuario']['rol']})")
            return data['usuario']
        else:
            print(f"Error: {data.get('error', 'Credenciales inválidas')}")
            return None

def listar_servicios_consola():
    print("\n--- Listado de Servicios ---")
    with app.test_client() as client:
        response = client.get('/servicios')
        servicios = response.get_json()
        
        if not servicios:
            print("No hay servicios disponibles")
            return
        
        for servicio in servicios:
            print(f"\nID: {servicio['id']}")
            print(f"Título: {servicio['titulo']}")
            print(f"Descripción: {servicio['descripcion']}")
            print(f"Precio: ${servicio['precio']}")
            print(f"Freelancer ID: {servicio['freelancer']}")

def crear_servicio_consola():
    print("\n--- Crear Nuevo Servicio ---")
    usuario = login_usuario_consola()
    if not usuario or usuario['rol'] != 'freelancer':
        print("Debes iniciar sesión como freelancer para crear servicios")
        return
    
    titulo = input("Título del servicio: ")
    descripcion = input("Descripción: ")
    precio = float(input("Precio: "))
    
    with app.test_client() as client:
        response = client.post('/servicios', json={
            'titulo': titulo,
            'descripcion': descripcion,
            'precio': precio,
            'freelancer_id': usuario['id']
        })
        
        data = response.get_json()
        if response.status_code == 201:
            print(f"Servicio creado: {data['mensaje']}")
        else:
            print(f"Error al crear servicio")

def crear_orden_consola():
    print("\n--- Crear Nueva Orden ---")
    usuario = login_usuario_consola()
    if not usuario or usuario['rol'] != 'cliente':
        print("Debes iniciar sesión como cliente para crear órdenes")
        return
    
    listar_servicios_consola()
    id_servicio = input("\nIngrese el ID del servicio que desea contratar: ")
    
    with app.test_client() as client:
        response = client.get('/servicios')
        servicios = response.get_json()
        servicio_seleccionado = next((s for s in servicios if str(s['id']) == id_servicio), None)
        
        if not servicio_seleccionado:
            print("ID de servicio no válido")
            return
        
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre FROM usuarios WHERE id=?", (servicio_seleccionado['freelancer'],))
            nombre_freelancer = cursor.fetchone()[0]
        
        response = client.post('/ordenes', json={
            'nombre_servicio': servicio_seleccionado['titulo'],
            'nombre_usuario': usuario['nombre'],
            'nombre_freelancer': nombre_freelancer,
            'descripcion': servicio_seleccionado['descripcion'],
            'precio': servicio_seleccionado['precio']
        })
        
        data = response.get_json()
        if response.status_code == 201:
            print(f"Orden creada: {data['mensaje']}")
        else:
            print(f"Error al crear orden")

def menu():
    while True:
        print("\n--- FreelanceYA ---")
        print("1. Registrar usuario")
        print("2. Listar servicios")
        print("3. Crear servicio (Freelancer)")
        print("4. Crear orden (Cliente)")
        print("5. Salir")
        
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            registrar_usuario_consola()
        elif opcion == "2":
            listar_servicios_consola()
        elif opcion == "3":
            crear_servicio_consola()
        elif opcion == "4":
            crear_orden_consola()
        elif opcion == "5":
            print("Saliendo...")
            break
        else:
            print("Opción no válida")

# ------------------ MAIN ------------------
if __name__ == '__main__':
    menu()