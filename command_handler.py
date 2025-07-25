# command_handler.py
# Author: Joan Cobeña
# Description: Módulo para manejar comandos relacionados con procesos.

from process_manager import crear_proceso, listar_procesos, eliminar_proceso, modificar_proceso

"""
    Procesa un comando de gestión de procesos.
    cmd: Comando a procesar.
    Retorna un mensaje indicando el resultado de la operación.
    Los comandos válidos son:
    - crear <id> <nombre> <prioridad>
    - listar
    - eliminar <id>
    - modificar <id> <campo> <valor>
"""
def procesar_comando(cmd):
    partes = cmd.strip().split()
    if not partes:
        return "Comando vacío."

    accion = partes[0].lower()

    try:
        if accion == "crear":
            _, id_, nombre, prioridad = partes
            ok, msg = crear_proceso(id_, nombre, prioridad)
            return msg
        elif accion == "listar":
            return listar_procesos()
        elif accion == "eliminar":
            _, id_ = partes
            ok, msg = eliminar_proceso(id_)
            return msg
        elif accion == "modificar":
            _, id_, campo, valor = partes
            ok, msg = modificar_proceso(id_, campo, valor)
            return msg
        else:
            return "Comando no reconocido."
    except ValueError:
        return "Número de argumentos inválido."
    except Exception as e:
        return f"Error al procesar comando: {str(e)}"
