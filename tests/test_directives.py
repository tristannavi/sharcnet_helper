import unittest
from pathlib import Path
from unittest.mock import patch

from sharcnet_helper.env import find_python_modules, find_python_version, make_venv

from fake_process import FakeProcess


class VenvTest(unittest.TestCase):
    @patch('subprocess.Popen')
    def test_find_python_modules(self, mock_popen):
        # Set the side effect of our fake Popen so that whenever it's called,
        # it returns an instance of our FakeProcess.
        mock_popen.side_effect = lambda *args, **kwargs: FakeProcess(args[0])

        # Call the function with a version string that forces the simulated command
        modules = find_python_modules("python/v1")

        # Check that our function parsed the output correctly.
        self.assertEqual(modules, ['Module1', 'Module2'])

    @patch('subprocess.Popen')
    def test_find_python_version(self, mock_popen):
        # Set the side effect of our fake Popen so that whenever it's called,
        # it returns an instance of our FakeProcess.
        mock_popen.side_effect = lambda *args, **kwargs: FakeProcess(args[0])

        # Call the function with a version string that forces the simulated command
        modules = find_python_version("v1")

        # Check that our function parsed the output correctly.
        self.assertEqual("python/v1", modules)

    @patch('subprocess.Popen')
    def test_make_venv(self, mock_popen):
        # Set the side effect of our fake Popen so that whenever it's called,
        # it returns an instance of our FakeProcess.
        mock_popen.side_effect = lambda *args, **kwargs: FakeProcess(args[0])

        # Call the function with a version string that forces the simulated command
        modules = make_venv("name", Path.home(), ["numpy"], "v1", ["scipy-stack"], file_name=None)

        # Check that our function parsed the output correctly.
        # self.assertEqual(modules, 'python/v1')


if __name__ == '__main__':
    unittest.main()
