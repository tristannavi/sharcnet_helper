import re
import shlex
import subprocess
import textwrap
from pathlib import Path
from time import sleep
from typing import List, Any


def make_job_name(*args: Any, sep: str) -> str:
    """
    Create a job name from the arguments.
    :param sep: the separator to use
    :type sep: str, required
    :param args: the arguments to use
    :type args: Any, required
    :rtype: str
    """
    return sep.join(str(arg) for arg in args)


class Directives:
    def __init__(self, mem: str, hours: int, modules: List[str], working_dir: Path = Path(__file__).parent,
                 minutes: int = 0, job_name: [str | None] = None, array_job: [int | List[int] | None] = None,
                 mail_type: [str | List[str] | None] = "FAIL", n_tasks: [int | None] = None, *args):
        """
        :param mem: the memory to allocate for the job
        :type mem: str, required
        :param hours: the number of hours to allocate for the job
        :type hours: int, required
        :param minutes: the number of minutes to allocate for the job
        :type minutes: int, optional
        :param working_dir: the working directory for the job, defaults to the current directory
        :type working_dir: Path, optional
        :param modules: the modules to load for the job
        :type modules: List[str], required
        :param job_name: the name of the job
        :type job_name: str | None, optional
        :param array_job: if this is an array job, the number of runs in the array
        :type array_job: int | List[int] | None, optional
        :param mail_type: the type of email to send. ALL, BEGIN, END, FAIL, REQUEUE, TIME_LIMIT, TIME_LIMIT_90, defaults to FAIL
        :type mail_type: str | List[str] | None, optional
        :rtype: None
        """

        self.mem = mem
        self.hours = hours
        self.minutes = minutes
        self.working_dir = working_dir
        self.modules = modules
        # if args is None:
        #     self.job_name = _make_job_name(*args)
        # else:
        self.job_name = job_name
        self.array_job = array_job
        self.mail_type = mail_type
        self.n_tasks = n_tasks

    def make_directives(self) -> str:
        def array_job_fn():
            if self.array_job is None:
                return ""
            elif type(self.array_job) == list:
                return "#SBATCH --array=" + ",".join(str(i) for i in self.array_job)
            else:
                return f"#SBATCH --array=1-{str(self.array_job)}"

        def n_tasks_fn():
            if self.n_tasks is None:
                return ""
            else:
                return f"#SBATCH --ntasks-per-node={str(self.n_tasks)}"

        directives = textwrap.dedent(f'''\
                    #!/bin/bash
                    #SBATCH --time={str(self.hours)}:{str(self.minutes) if self.minutes > 0 else "00"}:00
                    #SBATCH --account=def-houghten
                    #SBATCH --mem={self.mem}
                    {array_job_fn()}
                    {n_tasks_fn()}
                    #SBATCH --mail-user=tn13bm@brocku.ca
                    #SBATCH --mail-type={self.mail_type if type(self.mail_type) == str else ','.join(self.mail_type)}
                    #SBATCH --output={self.working_dir.absolute()}/output/slurm_{self.job_name}-{"%A_%a" if self.array_job is not None else "%A"}.out
                    #SBATCH --job-name={self.job_name}-{"%A_%a" if self.array_job is not None else "%A"}
                    
                    mkdir -p {self.working_dir.absolute()}/output
                    module load {' '.join(self.modules)}
                ''')

        return directives  # .replace("\n\n", "\n", 1)

    def __str__(self) -> str:
        """
        Return the directives as a string.
        :rtype: str
        """
        return self.make_directives()


def make_batch_file(directives: Directives, commands: List[str], file_name: str = "sbatch.sh") -> None:
    """
    Create a batch file for the job.
    :param directives: the directives to use
    :type directives: Directives, required
    :param commands: the commands to run
    :type commands: str, required
    :param file_name: the name of the file to create
    :type file_name: str, optional
    :rtype: None
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
    :type hours: float, optional
    :return: 0 to reset the counter
    :rtype: int
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
