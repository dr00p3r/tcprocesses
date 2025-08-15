# locustfile.py
from locust import User, task, between, events
import socket
import time

# Configuración del servidor
TCP_HOST = "localhost"
TCP_PORT = 12345

class TCPClient:
    def __init__(self):
        self.socket = None
        
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((TCP_HOST, TCP_PORT))
        # Leer mensaje de bienvenida
        self.socket.recv(1024)
    
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
    
    def close(self):
        if self.socket:
            self.socket.close()

class TCPUser(User):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        self.client = TCPClient()
        self.client.connect()
        self.process_counter = 0
    
    def on_stop(self):
        self.client.close()
    
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
    
    @task(1)
    def list_processes(self):
        self.client.send_command("LISTAR")