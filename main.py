# main.py
# Author: Joan Cobeña
# Description: Servidor de procesos que maneja comandos de gestión de procesos.

import socket
import threading
from command_handler import procesar_comando

"""
    Maneja la conexión de un cliente y procesa sus comandos.
    conn: Socket de conexión del cliente.
    addr: Dirección del cliente.
    Envía respuestas al cliente según los comandos recibidos.
"""
def manejar_cliente(conn, addr):
    print(f"[+] Conexión establecida con {addr}")
    conn.sendall(b"Servidor de procesos conectado.\n")

    while True:
        try:
            data = conn.recv(1024).decode(errors='ignore')
            if not data:
                break
            respuesta = procesar_comando(data)
            conn.sendall((respuesta + '\n').encode())
        except ConnectionResetError:
            break

    print(f"[-] Conexión cerrada con {addr}")
    conn.close()

"""
    Inicia el servidor y escucha conexiones entrantes.
    host: Dirección IP del servidor.
    port: Puerto en el que el servidor escucha.
"""
def iniciar_servidor(host="0.0.0.0", port=12345, max_conexiones=5):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(max_conexiones)
    print(f"Servidor escuchando en {host}:{port}")

    while True:
        conn, addr = server_socket.accept()
        hilo = threading.Thread(target=manejar_cliente, args=(conn, addr))
        hilo.start()

if __name__ == "__main__":
    iniciar_servidor()
