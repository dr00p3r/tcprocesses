#!/bin/bash
# run_performance_test.sh

USERS=${1:-20}
SPAWN_RATE=${2:-5}
DURATION=${3:-30s}

echo "Ejecutando prueba con $USERS usuarios."
echo "  Spawn rate: $SPAWN_RATE usuarios/segundo"
echo "  Duración: $DURATION"

locust -f locustfile.py \
    --headless \
    --users $USERS \
    --spawn-rate $SPAWN_RATE \
    --run-time $DURATION \
    --csv results \
    --html report.html


# Verificar objetivos con Python
python3 - << 'EOF'
import csv
import sys
import os

# Verificar si existe el archivo
if not os.path.exists('results_stats.csv'):
    print("ERROR: No se generó el archivo de resultados")
    sys.exit(1)

# Leer estadísticas de Locust
with open('results_stats.csv', 'r') as f:
    reader = csv.DictReader(f)
    stats = list(reader)

# Calcular métricas
total_requests = 0
total_failures = 0
p95_values = []

for stat in stats:
    if stat['Name'] != 'Aggregated':
        total_requests += int(stat['Request Count'])
        total_failures += int(stat['Failure Count'])

# Obtener datos agregados
aggregated = next((s for s in stats if s['Name'] == 'Aggregated'), None)

if aggregated:
    p95 = float(aggregated['95%'])
    success_rate = 1 - (int(aggregated['Failure Count']) / int(aggregated['Request Count'])) if int(aggregated['Request Count']) > 0 else 0
else:
    print("ERROR: No se encontraron datos agregados")
    sys.exit(1)

print(f"\n=== RESULTADOS ===")
print(f"Total solicitudes: {aggregated['Request Count']}")
print(f"Solicitudes fallidas: {aggregated['Failure Count']}")
print(f"Tasa de éxito: {success_rate*100:.2f}%")
print(f"P95: {p95:.2f}ms")

# Verificar objetivos
p95_ok = p95 < 700
success_ok = success_rate >= 0.95

print(f"\n=== VERIFICACIÓN DE OBJETIVOS ===")
print(f"P95 < 700ms: {'PASÓ' if p95_ok else 'FALLÓ'} ({p95:.2f}ms)")
print(f"Tasa éxito >= 95%: {'PASÓ' if success_ok else 'FALLÓ'} ({success_rate*100:.2f}%)")

if p95_ok and success_ok:
    print("\nPRUEBA EXITOSA: Todos los objetivos cumplidos")
    sys.exit(0)
else:
    print("\nPRUEBA FALLIDA: No se cumplieron todos los objetivos")
    sys.exit(1)
EOF

# Capturar el código de salida
exit_code=$?

echo -e "\nReporte HTML generado: report.html"
echo "Datos CSV generados: results_*.csv"

exit $exit_code