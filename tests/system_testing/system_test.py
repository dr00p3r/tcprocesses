# system_tests.py
import asyncio
import sys

HOST = "localhost"
PORT = 12345

async def send_command(reader, writer, command):
    """
    Función auxiliar para enviar un comando y recibir la respuesta del servidor.
    """
    print(f"\n-> Enviando comando: {command.strip()}")
    writer.write(command.encode('utf-8'))
    await writer.drain()

    # Leer la respuesta del servidor línea por línea
    response_lines = []
    while True:
        try:
            line = await asyncio.wait_for(reader.readline(), timeout=3.0)
            if not line:
                break
            response_lines.append(line.decode('utf-8').strip())
            # Si la respuesta no es un DATOS, normalmente termina en una línea.
            # Los comandos LISTAR y AYUDA pueden tener varias líneas.
            if not line.startswith(b"DATOS|"):
                break
        except asyncio.TimeoutError:
            print("Tiempo de espera agotado al recibir respuesta.")
            break
        
    response = "\n".join(response_lines)
    print(f"<- Recibido del servidor:\n{response}")
    return response

async def run_tests():
    """
    Función principal que ejecuta todos los escenarios de prueba.
    """
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        print(f"✅ Conectado al servidor en {HOST}:{PORT}")
        
        # 1. Recibir mensaje de bienvenida
        initial_msg = await reader.readline()
        print(f"<- Mensaje de bienvenida: {initial_msg.decode('utf-8').strip()}")

        # 2. Prueba: Crear un proceso
        print("\n--- TEST: CREAR PROCESO ---")
        response = await send_command(reader, writer, "CREAR|proceso_A|baja\n")
        assert "OK|Proceso 1 creado." in response, f"Fallo al crear proceso. Respuesta: {response}"
        print("✅ Proceso creado exitosamente.")

        # 3. Prueba: Listar procesos
        print("\n--- TEST: LISTAR PROCESOS ---")
        response = await send_command(reader, writer, "LISTAR\n")
        assert "DATOS|1: {'nombre': 'proceso_A', 'prioridad': 'baja', 'estado': 'activo'}" in response, f"Fallo al listar procesos. Respuesta: {response}"
        print("✅ Proceso listado correctamente.")

        # 4. Prueba: Modificar un proceso
        print("\n--- TEST: MODIFICAR PROCESO ---")
        response = await send_command(reader, writer, "MODIFICAR|1|prioridad|alta\n")
        assert "OK|Proceso 1 actualizado." in response, f"Fallo al modificar proceso. Respuesta: {response}"
        
        # 5. Prueba: Listar de nuevo para verificar la modificación
        response = await send_command(reader, writer, "LISTAR\n")
        assert "DATOS|1: {'nombre': 'proceso_A', 'prioridad': 'alta', 'estado': 'activo'}" in response, f"Fallo al verificar modificación. Respuesta: {response}"
        print("✅ Proceso modificado exitosamente.")
        
        # 6. Prueba: Eliminar un proceso
        print("\n--- TEST: ELIMINAR PROCESO ---")
        response = await send_command(reader, writer, "ELIMINAR|1\n")
        assert "OK|Proceso 1 eliminado." in response, f"Fallo al eliminar proceso. Respuesta: {response}"
        print("✅ Proceso eliminado exitosamente.")

        # 7. Prueba: Listar para verificar la eliminación
        response = await send_command(reader, writer, "LISTAR\n")
        assert "DATOS|Sin procesos." in response, f"Fallo al verificar eliminación. Respuesta: {response}"
        print("✅ Eliminación verificada.")
        
        # 8. Prueba: Comandos de error
        print("\n--- TEST: COMANDOS DE ERROR ---")
        response = await send_command(reader, writer, "COMANDO_INEXISTENTE\n")
        assert "ERROR|Comando no reconocido." in response, f"Fallo en comando no reconocido. Respuesta: {response}"
        
        response = await send_command(reader, writer, "CREAR|proceso_B\n")
        assert "ERROR|Argumentos inválidos para CREAR." in response, f"Fallo en argumentos invalidos para crear. Respuesta: {response}"
        
        response = await send_command(reader, writer, "ELIMINAR|99\n")
        assert "ERROR|Proceso no encontrado." in response, f"Fallo en eliminar inexistente. Respuesta: {response}"
        print("✅ Gestión de errores probada con éxito.")

        # 9. Desconexión
        print("\n--- TEST: SALIR Y DESCONECTAR ---")
        writer.close()
        await writer.wait_closed()
        print("✅ Conexión cerrada correctamente.")

    except ConnectionRefusedError:
        print("❌ Error: Conexión rechazada. Asegúrate de que el servidor está escuchando.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado durante las pruebas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("Iniciando pruebas del sistema...")
    asyncio.run(run_tests())