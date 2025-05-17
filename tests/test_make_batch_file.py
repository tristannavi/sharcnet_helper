from pathlib import Path

from sharcnet_helper.directives import Directives, PythonDirectives
from sharcnet_helper.sbatch_utils import make_batch_file


def test_from_directives():
    directives = PythonDirectives("2", 2, [""], working_dir=Path.home(), env_path=Path("/home/python/venv"), python_version="1")
    # make_batch_file("output", 5, directives=directives, commands=["python -u test.py"])
    print(directives.make_directives("test"))
