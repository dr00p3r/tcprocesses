# process_manager.py
# Author: Joan Cobeña
# Description: Módulo para gestionar procesos en memoria.
import threading

#Arreglo de procesos en memoria para simular un gestor de procesos.
procesos = {}

# ID del próximo proceso a crear.
next_pid = 1

# Lock para manejar concurrencia en el acceso a procesos
# Esto es importante para evitar condiciones de carrera en un entorno multihilo.
lock = threading.Lock()

"""    
    Crea un nuevo proceso.
    nombre: Nombre del proceso.
    prioridad: Prioridad del proceso.
    Retorna una tupla (exito, mensaje).
    Si el proceso ya existe, retorna False y un mensaje de Proceso ya existe.
    Si el proceso se crea correctamente, retorna True y un mensaje de Proceso creado.
"""
def crear_proceso(nombre, prioridad):
    global next_pid
    with lock:
        pid = str(next_pid)
        
        procesos[pid] = {
            "nombre": nombre,
            "prioridad": prioridad,
            "estado": "activo"
        }
        next_pid += 1
        return True, f"Proceso {pid} creado."

""" 
    Lista todos los procesos existentes.
    Retorna una cadena con la lista de procesos o 
    un mensaje indicando que no hay procesos.
"""
def listar_procesos():
    with lock:
        if not procesos:
            return "Sin procesos."
        return "\n".join([f"{pid}: {info}" for pid, info in procesos.items()])

"""
    Elimina un proceso existente.
    pid: ID del proceso a eliminar.
    Retorna una tupla (exito, mensaje).
    Si el proceso no existe, retorna False y un mensaje de Proceso no encontrado.
    Si el proceso se elimina correctamente, retorna True y un mensaje de Proceso eliminado.
"""
def eliminar_proceso(pid):
    with lock:
        if pid in procesos:
            del procesos[pid]
            return True, f"Proceso {pid} eliminado."
        return False, "Proceso no encontrado."

"""
    Modifica un campo de un proceso existente.
    pid: ID del proceso a modificar.
    campo: Campo a modificar (nombre, prioridad, estado).
    valor: Nuevo valor para el campo.
    Retorna una tupla (exito, mensaje).
    Si el proceso no existe o el campo es inválido, 
    retorna False y un mensaje de campo inválido.
    Si el proceso se modifica correctamente,
    retorna True y un mensaje de Proceso actualizado.
"""
def modificar_proceso(pid, campo, valor):
    with lock:
        if pid not in procesos:
            return False, "Proceso no encontrado."
        if campo not in procesos[pid]:
            return False, "Campo inválido."
        procesos[pid][campo] = valor
        return True, f"Proceso {pid} actualizado."

"""
    Utilidad para limpiar todos los procesos. Útil en tests.
"""
def reiniciar_procesos():
    procesos.clear()
