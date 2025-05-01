import re
import shlex
import subprocess
from time import sleep
from typing import List, Any

from sharcnet_helper.directives import Directives


def make_job_name(*args: Any, sep: str) -> str:
    """
    Create a job name from the arguments.
    :param sep: the separator to use
    :param args: the arguments to use
    """
    return sep.join(str(arg) for arg in args)


def make_batch_file(directives: Directives, commands: List[str], file_name: str = "sbatch.sh") -> None:
    """
    Create a batch file for the job.
    :param directives: the directives to use
    :param commands: the commands to run
    :param file_name: the name of the file to create
    """
    with open(file_name, "w") as f:
        f.write(str(directives) + "\n")
        for command in commands:
            variables = re.findall(r"\$[0-9]*", command)
            command = re.sub("^python [^-]", "python -u", command)  # Add -u to the python command to flush output
            for var in variables:  # Replace $1 with "$1" to prevent bash from interpreting it
                command = command.replace(var, f'"{var}"')
                command = command.replace('""', '"')
            f.write(command + "\n")


def sleep_and_write(user: str, hours: float = 0.5) -> int:
    """
    Checks if there are still matching jobs in the queue every 30 minutes.
    Create and delete a temp folder to ensure IO operations are done.

    :param user: The username to check the queue for
    :param hours: Number of hours to sleep, default is 0.5 (30 minutes)
    :return: 0 to reset the counter
    """
    while True:
        result = subprocess.run(
            f"squeue -u {user} | grep {user}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # get output as a string rather than bytes
        )

        if result.returncode != 0:
            break

        sleep(hours * 60 * 60)
        subprocess.call(shlex.split(f"mkdir -p temp"))
        subprocess.call(shlex.split(f"rm -rf temp"))
    return 0
