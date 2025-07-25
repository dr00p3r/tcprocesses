# tests/test_commands.py
import unittest
from process_manager import crear_proceso, listar_procesos, eliminar_proceso, modificar_proceso, reiniciar_procesos

class TestProcessManager(unittest.TestCase):

    def setUp(self):
        reiniciar_procesos()

    def test_crear_y_listar(self):
        ok, msg = crear_proceso("p1", "backup", "5")
        self.assertTrue(ok)
        self.assertIn("p1", listar_procesos())
        print(msg)

    def test_proceso_duplicado(self):
        crear_proceso("p1", "backup", "5")
        ok, msg = crear_proceso("p1", "otro", "3")
        self.assertFalse(ok)
        self.assertIn("ya existe", msg.lower())
        print(msg)

    def test_eliminar(self):
        crear_proceso("p1", "backup", "5")
        ok, msg = eliminar_proceso("p1")
        self.assertTrue(ok)
        self.assertNotIn("p1", listar_procesos())
        print(msg)

    def test_modificar(self):
        crear_proceso("p1", "backup", "5")
        ok, msg = modificar_proceso("p1", "prioridad", "10")
        self.assertTrue(ok)
        print(msg)

    def test_modificar_invalido(self):
        crear_proceso("p1", "backup", "5")
        ok, msg = modificar_proceso("p1", "invalido", "10")
        self.assertFalse(ok)
        print(msg)

if __name__ == "__main__":
    unittest.main()
