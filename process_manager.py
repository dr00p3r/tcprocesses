# process_manager.py
# Author: Joan Cobeña
# Description: Módulo para gestionar procesos en memoria.

#Arreglo de procesos en memoria para simular un gestor de procesos.
procesos = {}

"""    
    Crea un nuevo proceso.
    id_: ID del proceso a crear.
    nombre: Nombre del proceso.
    prioridad: Prioridad del proceso.
    Retorna una tupla (exito, mensaje).
    Si el proceso ya existe, retorna False y un mensaje de Proceso ya existe.
    Si el proceso se crea correctamente, retorna True y un mensaje de Proceso creado.
"""
def crear_proceso(id_, nombre, prioridad):
    if id_ in procesos:
        return False, "Proceso ya existe."
    procesos[id_] = {
        "nombre": nombre,
        "prioridad": prioridad,
        "estado": "activo"
    }
    return True, f"Proceso {id_} creado."

""" 
    Lista todos los procesos existentes.
    Retorna una cadena con la lista de procesos o 
    un mensaje indicando que no hay procesos.
"""
def listar_procesos():
    if not procesos:
        return "Sin procesos."
    return "\n".join([f"{pid}: {info}" for pid, info in procesos.items()])

"""
    Elimina un proceso existente.
    id_: ID del proceso a eliminar.
    Retorna una tupla (exito, mensaje).
    Si el proceso no existe, retorna False y un mensaje de Proceso no encontrado.
    Si el proceso se elimina correctamente, retorna True y un mensaje de Proceso eliminado.
"""
def eliminar_proceso(id_):
    if id_ in procesos:
        del procesos[id_]
        return True, f"Proceso {id_} eliminado."
    return False, "Proceso no encontrado."

"""
    Modifica un campo de un proceso existente.
    id_: ID del proceso a modificar.
    campo: Campo a modificar (nombre, prioridad, estado).
    valor: Nuevo valor para el campo.
    Retorna una tupla (exito, mensaje).
    Si el proceso no existe o el campo es inválido, 
    retorna False y un mensaje de campo inválido.
    Si el proceso se modifica correctamente,
    retorna True y un mensaje de Proceso actualizado.
"""
def modificar_proceso(id_, campo, valor):
    if id_ not in procesos:
        return False, "Proceso no encontrado."
    if campo not in procesos[id_]:
        return False, "Campo inválido."
    procesos[id_][campo] = valor
    return True, f"Proceso {id_} actualizado."

"""
    Utilidad para limpiar todos los procesos. Útil en tests.
"""
def reiniciar_procesos():
    procesos.clear()
