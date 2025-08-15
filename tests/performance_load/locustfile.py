# locustfile.py
# Description: Pruebas de carga y rendimiento (Locust) contra el servidor TCP de procesos.

from locust import User, task, between, events
import socket
import time

# Configuración del servidor
TCP_HOST = "localhost"
TCP_PORT = 12345

"""
    Cliente TCP simple para interactuar con el servidor de procesos.
    Métodos:
    - connect(): Establece conexión y lee el banner de bienvenida.
    - send_command(command): Envía un comando y reporta métricas a Locust.
    - close(): Cierra el socket si está abierto.
"""
class TCPClient:
    """
        Inicializa el cliente sin conexión activa.
    """
    def __init__(self):
        self.socket = None
        
    """
        Establece la conexión con el servidor y consume el mensaje de bienvenida.
    """
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((TCP_HOST, TCP_PORT))
        # Leer mensaje de bienvenida
        self.socket.recv(1024)
    
    """
        Envía un comando al servidor y mide el tiempo de respuesta.
        command: Cadena de comando (sin salto, se añade '\n' al enviar).
        Reporta el resultado a Locust mediante events.request.fire.
        Retorna: Respuesta decodificada y sin espacios finales.
    """
    def send_command(self, command):
        start_time = time.time()
        try:
            self.socket.send(f"{command}\n".encode())
            response = self.socket.recv(1024).decode().strip()
            total_time = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="TCP",
                name=command.split('|')[0],
                response_time=total_time,
                response_length=len(response),
                response=response,
                context={},
                exception=None
            )
            return response
        except Exception as e:
            total_time = (time.time() - start_time) * 1000
            events.request.fire(
                request_type="TCP",
                name=command.split('|')[0],
                response_time=total_time,
                response_length=0,
                exception=e,
                context={}
            )
            raise e
    
    """
        Cierra el socket si existe.
    """
    def close(self):
        if self.socket:
            self.socket.close()

"""
    Usuario de Locust que mantiene una conexión TCP persistente para ejecutar tareas.
    wait_time: Pausas aleatorias entre tareas.
    on_start/on_stop: Ciclo de vida para abrir/cerrar la conexión.
    Tareas:
    - create_and_delete_process: Crear, listar, modificar y eliminar un proceso.
    - list_processes: Listar procesos.
"""
class TCPUser(User):
    wait_time = between(0.1, 0.5)
    
    """
        Al iniciar, crea el cliente TCP, conecta y reinicia el contador de procesos.
    """
    def on_start(self):
        self.client = TCPClient()
        self.client.connect()
        self.process_counter = 0
    
    """
        Al finalizar, cierra la conexión TCP.
    """
    def on_stop(self):
        self.client.close()
    
    """
        Crea un proceso, lo lista, lo modifica y finalmente lo elimina.
        Peso de tarea: 4.
    """
    @task(4)
    def create_and_delete_process(self):
        # Crear proceso
        self.process_counter += 1
        process_name = f"proceso_{self.environment.runner.user_count}_{self.process_counter}"
        response = self.client.send_command(f"CREAR|{process_name}|alta")
        
        # Extraer ID del proceso
        if "OK|Proceso" in response:
            process_id = response.split()[1]
            
            # Listar procesos
            self.client.send_command("LISTAR")
            
            # Modificar proceso
            self.client.send_command(f"MODIFICAR|{process_id}|prioridad|baja")
            
            # Eliminar proceso
            self.client.send_command(f"ELIMINAR|{process_id}")
    
    """
        Lista los procesos existentes.
        Peso de tarea: 1.
    """
    @task(1)
    def list_processes(self):
        self.client.send_command("LISTAR")
