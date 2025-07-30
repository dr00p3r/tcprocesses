# tests/test_commands.py
import unittest
from process_manager import crear_proceso, listar_procesos, eliminar_proceso, modificar_proceso, reiniciar_procesos

class TestProcessManager(unittest.TestCase):

    def setUp(self):
        reiniciar_procesos()

    def test_crear_y_listar(self):
        ok, msg = crear_proceso("backup", "5")
        self.assertTrue(ok)
        self.assertIn("1", listar_procesos())
        print(msg)

    def test_eliminar(self):
        reiniciar_procesos()
        crear_proceso("backup", "5")
        ok, msg = eliminar_proceso("1")
        self.assertTrue(ok)
        self.assertNotIn("1", listar_procesos())
        print(msg)

    def test_modificar(self):
        reiniciar_procesos()
        crear_proceso("backup", "5")
        ok, msg = modificar_proceso("1", "prioridad", "10")
        self.assertTrue(ok)
        print(msg)

    def test_modificar_invalido(self):
        reiniciar_procesos()
        crear_proceso("backup", "5")
        ok, msg = modificar_proceso("1", "invalido", "10")
        self.assertFalse(ok)
        print(msg)

if __name__ == "__main__":
    unittest.main()
