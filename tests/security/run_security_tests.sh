#!/bin/bash
# run_security_tests.sh

echo "🔒 Iniciando pruebas de seguridad del servidor TCP"

# Verificar si el servidor está corriendo
nc -zv localhost 12345 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: El servidor no está disponible en localhost:12345"
    exit 1
fi

# Ejecutar pruebas de seguridad
python3 security_tests.py

# Verificar código de salida
if [ $? -eq 0 ]; then
    echo -e "\n✅ Servidor SEGURO: No se encontraron vulnerabilidades"
else
    echo -e "\n⚠️  Servidor VULNERABLE: Revisa los reportes generados"
fi

# Abrir reporte HTML si existe
if command -v xdg-open &> /dev/null; then
    latest_report=$(ls -t security_report_*.html | head -1)
    if [ -f "$latest_report" ]; then
        echo "📊 Abriendo reporte: $latest_report"
        xdg-open "$latest_report"
    fi
fi