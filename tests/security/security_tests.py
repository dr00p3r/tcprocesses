# security_tests.py
# Description: Pruebas de seguridad del servidor TCP de procesos (inyección, overflow, DoS, traversal, format string, auth bypass).

import asyncio
import sys
import random
import string
import json
from datetime import datetime

HOST = "localhost"
PORT = 12345

"""
    Clase ejecutora de pruebas de seguridad contra el servidor TCP.
    Mantiene lista de vulnerabilidades y resultados detallados de cada prueba.
"""
class SecurityTester:
    """
        Inicializa contenedores de resultados y vulnerabilidades.
    """
    def __init__(self):
        self.vulnerabilities = []
        self.test_results = []
        
    """
        Establece conexión con el servidor y consume el mensaje de bienvenida.
        Retorna: (reader, writer) o (None, None) ante error.
    """
    async def connect(self):
        try:
            reader, writer = await asyncio.open_connection(HOST, PORT)
            # Leer mensaje de bienvenida
            await reader.readline()
            return reader, writer
        except Exception as e:
            print(f"ERROR conectando: {e}")
            return None, None
    
    """
        Envía un payload y retorna la primera línea de respuesta (o TIMEOUT/ERROR).
        reader: StreamReader activo.
        writer: StreamWriter activo.
        payload: Cadena a enviar (debe incluir '\n' si aplica).
    """
    async def send_payload(self, reader, writer, payload):
        try:
            writer.write(payload.encode('utf-8'))
            await writer.drain()
            response = await asyncio.wait_for(reader.readline(), timeout=2.0)
            return response.decode('utf-8', errors='ignore').strip()
        except asyncio.TimeoutError:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    """
        Prueba de inyección de comandos.
        Marca vulnerable si la respuesta contiene indicios de ejecución de comandos del sistema.
    """
    async def test_command_injection(self):
        print("\nTest 1: Inyección de Comandos")
        
        payloads = [
            "CREAR|proceso1|alta;ls -la\n",
            "CREAR|proceso1|alta && cat /etc/passwd\n",
            "CREAR|proceso1|alta`whoami`\n",
            "CREAR|proceso1|alta$(whoami)\n",
            "CREAR|proceso1|alta\n;id\n",
            "MODIFICAR|1|prioridad|alta;rm -rf /\n",
            "ELIMINAR|1 OR 1=1\n",
            "CREAR|proceso1|alta\x00whoami\n",
        ]
        
        for payload in payloads:
            reader, writer = await self.connect()
            if not reader:
                continue
                
            response = await self.send_payload(reader, writer, payload)
            
            # Verificar si hay indicios de ejecución de comandos
            dangerous_outputs = ['root', 'uid=', 'gid=', 'passwd', 'total', 'drwx']
            is_vulnerable = any(output in response.lower() for output in dangerous_outputs)
            
            result = {
                'test': 'Command Injection',
                'payload': payload.strip(),
                'response': response[:100] + '...' if len(response) > 100 else response,
                'vulnerable': is_vulnerable
            }
            
            self.test_results.append(result)
            
            if is_vulnerable:
                self.vulnerabilities.append(f"Command Injection: {payload.strip()}")
                print(f"  VULNERABLE con: {payload.strip()}")
            else:
                print(f"  Seguro contra: {payload.strip()}")
            
            writer.close()
            await writer.wait_closed()
    
    """
        Prueba de desbordamiento de buffer.
        Marca vulnerable por TIMEOUT, respuesta vacía o errores de conexión.
    """
    async def test_buffer_overflow(self):
        print("\nTest 2: Buffer Overflow")
        
        test_cases = [
            ('Comando largo', 'A' * 1000),
            ('Nombre proceso largo', f"CREAR|{'B' * 5000}|alta\n"),
            ('Prioridad larga', f"CREAR|proceso1|{'C' * 5000}\n"),
            ('ID muy largo', f"MODIFICAR|{'9' * 5000}|prioridad|alta\n"),
            ('Múltiples pipes', f"CREAR|{'|' * 1000}\n"),
            ('Caracteres null', f"CREAR|proceso\x00" + 'D' * 1000 + "|alta\n"),
            ('Unicode overflow', f"CREAR|{'你' * 2000}|alta\n"),
        ]
        
        for test_name, payload in test_cases:
            reader, writer = await self.connect()
            if not reader:
                continue
            
            response = await self.send_payload(reader, writer, payload)
            
            # Verificar si el servidor crasheó o respondió anormalmente
            is_vulnerable = response in ["TIMEOUT", ""] or ("ERROR" in response and "Connection" in response)
            
            result = {
                'test': 'Buffer Overflow',
                'payload': f"{test_name} ({len(payload)} bytes)",
                'response': response[:50] + '...' if len(response) > 50 else response,
                'vulnerable': is_vulnerable
            }
            
            self.test_results.append(result)
            
            if is_vulnerable:
                self.vulnerabilities.append(f"Buffer Overflow: {test_name}")
                print(f"  VULNERABLE: {test_name}")
            else:
                print(f"  Seguro: {test_name}")
            
            writer.close()
            await writer.wait_closed()
    
    """
        Prueba de ataques de denegación de servicio (DoS).
        Incluye: agotamiento de conexiones y flood de comandos.
    """
    async def test_dos_attacks(self):
        print("\nTest 4: Denial of Service (DoS)")
        
        # Test 1: Conexiones múltiples sin cerrar
        print("  Probando conexiones múltiples...")
        connections = []
        try:
            for i in range(100):
                reader, writer = await self.connect()
                if reader:
                    connections.append((reader, writer))
            
            # Verificar si aún podemos conectar
            test_reader, test_writer = await self.connect()
            dos_vulnerable = test_reader is None
            
            if dos_vulnerable:
                self.vulnerabilities.append("DoS: Agotamiento de conexiones")
                print("  VULNERABLE: Límite de conexiones alcanzado")
            else:
                print("  Seguro: Maneja múltiples conexiones")
                test_writer.close()
            
            # Cerrar todas las conexiones
            for reader, writer in connections:
                writer.close()
                await writer.wait_closed()
                
        except Exception as e:
            print(f"  Error en prueba DoS: {e}")
        
        # Test 2: Comandos rápidos
        print("  Probando flood de comandos...")
        reader, writer = await self.connect()
        if reader:
            start_time = asyncio.get_event_loop().time()
            for i in range(1000):
                await self.send_payload(reader, writer, f"CREAR|flood_{i}|alta\n")
            
            duration = asyncio.get_event_loop().time() - start_time
            print(f"  1000 comandos en {duration:.2f}s")
            writer.close()
            await writer.wait_closed()
    
    """
        Prueba de path traversal.
        Marca vulnerable si la respuesta aparenta exposición de archivos sensibles.
    """
    async def test_path_traversal(self):
        print("\nTest 5: Path Traversal")
        
        payloads = [
            "CREAR|../../../etc/passwd|alta\n",
            "CREAR|proceso1|../../root/.ssh/id_rsa\n",
            "MODIFICAR|1|prioridad|../../../etc/shadow\n",
            "CREAR|C:\\Windows\\System32\\config\\sam|alta\n",
            "CREAR|proceso1|alta\n../../\n",
        ]
        
        for payload in payloads:
            reader, writer = await self.connect()
            if not reader:
                continue
            
            response = await self.send_payload(reader, writer, payload)
            
            # Verificar si hay acceso a archivos del sistema
            path_indicators = ['passwd', 'shadow', 'root:', 'bin:', 'Windows', 'System32']
            is_vulnerable = any(indicator in response for indicator in path_indicators)
            
            result = {
                'test': 'Path Traversal',
                'payload': payload.strip(),
                'response': response[:100] + '...' if len(response) > 100 else response,
                'vulnerable': is_vulnerable
            }
            
            self.test_results.append(result)
            
            if is_vulnerable:
                self.vulnerabilities.append(f"Path Traversal: {payload.strip()}")
                print(f"  VULNERABLE con: {payload.strip()}")
            else:
                print(f"  Seguro contra: {payload.strip()}")
            
            writer.close()
            await writer.wait_closed()
    
    """
        Prueba de vulnerabilidades de cadenas de formato (format string).
        Busca indicadores típicos en la respuesta.
    """
    async def test_format_string(self):
        print("\nTest 6: Format String")
        
        payloads = [
            "CREAR|%s%s%s%s%s|alta\n",
            "CREAR|proceso_%x_%x_%x|alta\n",
            "CREAR|%n%n%n|alta\n",
            "MODIFICAR|1|prioridad|%08x.%08x.%08x\n",
            "CREAR|{0.__class__.__bases__[0].__subclasses__()}|alta\n",
        ]
        
        for payload in payloads:
            reader, writer = await self.connect()
            if not reader:
                continue
            
            response = await self.send_payload(reader, writer, payload)
            
            # Buscar indicios de format string
            format_indicators = ['0x', 'segmentation', 'fault', 'core dumped', 'class']
            is_vulnerable = any(indicator in response.lower() for indicator in format_indicators)
            
            result = {
                'test': 'Format String',
                'payload': payload.strip(),
                'response': response[:100] + '...' if len(response) > 100 else response,
                'vulnerable': is_vulnerable
            }
            
            self.test_results.append(result)
            
            if is_vulnerable:
                self.vulnerabilities.append(f"Format String: {payload.strip()}")
                print(f"  VULNERABLE con: {payload.strip()}")
            else:
                print(f"  Seguro contra: {payload.strip()}")
            
            writer.close()
            await writer.wait_closed()
    
    """
        Prueba de bypass de autenticación (si aplica).
        Marca vulnerable si comandos privilegiados se aceptan con 'OK'.
    """
    async def test_authentication_bypass(self):
        print("\nTest 7: Authentication Bypass")
        
        payloads = [
            "ADMIN|LISTAR\n",
            "SUDO|ELIMINAR|1\n",
            "\x00CREAR|proceso_admin|alta\n",
            "AUTH|admin|admin\n",
            "CREAR|proceso1|alta|admin=true\n",
        ]
        
        for payload in payloads:
            reader, writer = await self.connect()
            if not reader:
                continue
            
            response = await self.send_payload(reader, writer, payload)
            
            # Verificar si se ejecutó un comando privilegiado
            auth_indicators = ['admin', 'privilege', 'unauthorized', 'denied']
            is_vulnerable = 'OK' in response and any(payload.upper().startswith(cmd) for cmd in ['ADMIN', 'SUDO'])
            
            result = {
                'test': 'Authentication Bypass',
                'payload': payload.strip(),
                'response": response[:100] + "..." if len(response) > 100 else response,
                'vulnerable': is_vulnerable
            }
            
            self.test_results.append(result)
            
            if is_vulnerable:
                self.vulnerabilities.append(f"Auth Bypass: {payload.strip()}")
                print(f"  VULNERABLE con: {payload.strip()}")
            else:
                print(f"  Seguro contra: {payload.strip()}")
            
            writer.close()
            await writer.wait_closed()
    
    """
        Genera y guarda reportes JSON y HTML del resultado de las pruebas.
        Retorna: (ruta_html, ruta_json).
    """
    def generate_report(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report = {
            'scan_date': datetime.now().isoformat(),
            'target': f"{HOST}:{PORT}",
            'total_tests': len(self.test_results),
            'vulnerabilities_found': len(self.vulnerabilities),
            'test_results': self.test_results,
            'vulnerabilities': self.vulnerabilities
        }
        
        # Guardar reporte JSON
        with open(f'security_report_{timestamp}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generar reporte HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Reporte de Seguridad TCP</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .vulnerable {{ background-color: #e74c3c; color: white; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .secure {{ background-color: #27ae60; color: white; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #34495e; color: white; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat-box {{ text-align: center; padding: 20px; background-color: #ecf0f1; border-radius: 5px; }}
        .stat-number {{ font-size: 36px; font-weight: bold; color: #2c3e50; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reporte de Seguridad - Servidor TCP</h1>
        <p>Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Objetivo: {HOST}:{PORT}</p>
    </div>
    
    <div class="summary">
        <div class="stat-box">
            <div class="stat-number">{len(self.test_results)}</div>
            <div>Pruebas Totales</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #e74c3c;">{len(self.vulnerabilities)}</div>
            <div>Vulnerabilidades</div>
        </div>
        <div class="stat-box">
            <div class="stat-number" style="color: #27ae60;">{len(self.test_results) - len(self.vulnerabilities)}</div>
            <div>Pruebas Seguras</div>
        </div>
    </div>
"""
        
        if self.vulnerabilities:
            html_content += """
    <div class="test-section">
        <h2>Vulnerabilidades Encontradas</h2>
"""
            for vuln in self.vulnerabilities:
                html_content += f'        <div class="vulnerable">{vuln}</div>\n'
            html_content += "    </div>\n"
        
        # Tabla de resultados detallados
        html_content += """
    <div class="test-section">
        <h2>Resultados Detallados</h2>
        <table>
            <tr>
                <th>Tipo de Prueba</th>
                <th>Payload</th>
                <th>Respuesta</th>
                <th>Estado</th>
            </tr>
"""
        
        for result in self.test_results:
            status = '<span style="color: red;">Vulnerable</span>' if result['vulnerable'] else '<span style="color: green;">Seguro</span>'
            html_content += f"""
            <tr>
                <td>{result['test']}</td>
                <td><code>{result['payload']}</code></td>
                <td><code>{result['response']}</code></td>
                <td>{status}</td>
            </tr>
"""
        
        html_content += """
        </table>
    </div>

</body>
</html>
"""
        
        with open(f'security_report_{timestamp}.html', 'w') as f:
            f.write(html_content)
        
        return f'security_report_{timestamp}.html', f'security_report_{timestamp}.json'

"""
    Ejecuta todas las pruebas de seguridad y genera reportes.
    Retorna True si no se detectaron vulnerabilidades.
"""
async def run_security_tests():
    print("="*60)
    print("🔒 INICIANDO PRUEBAS DE SEGURIDAD")
    print("="*60)
    print(f"Objetivo: {HOST}:{PORT}")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SecurityTester()
    
    # Ejecutar todas las pruebas
    await tester.test_command_injection()
    await tester.test_buffer_overflow()
    await tester.test_dos_attacks()
    await tester.test_path_traversal()
    await tester.test_format_string()
    await tester.test_authentication_bypass()
    
    # Generar reporte
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)
    
    print(f"Total de pruebas: {len(tester.test_results)}")
    print(f"Vulnerabilidades encontradas: {len(tester.vulnerabilities)}")
    
    if tester.vulnerabilities:
        print("\nVULNERABILIDADES DETECTADAS:")
        for vuln in tester.vulnerabilities:
            print(f"   - {vuln}")
    else:
        print("\nNo se encontraron vulnerabilidades")
    
    html_file, json_file = tester.generate_report()
    print(f"\nReportes generados:")
    print(f"   - HTML: {html_file}")
    print(f"   - JSON: {json_file}")
    
    return len(tester.vulnerabilities) == 0

"""
    Punto de entrada del script de pruebas de seguridad.
"""
if __name__ == "__main__":
    try:
        is_secure = asyncio.run(run_security_tests())
        sys.exit(0 if is_secure else 1)
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\nError durante las pruebas: {e}")
        sys.exit(1)
