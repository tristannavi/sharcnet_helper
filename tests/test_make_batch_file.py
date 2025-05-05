from pathlib import Path

from sharcnet_helper.directives import Directives
from sharcnet_helper.sbatch_utils import make_batch_file


def test_from_directives():
    directives = Directives("2", 2, [""], Path.home())
    make_batch_file("output", 5, directives=directives, commands=["python -u test.py"])
