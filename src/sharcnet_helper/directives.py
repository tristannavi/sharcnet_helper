import subprocess
import textwrap
import tomllib
from pathlib import Path
from typing import List

from sharcnet_helper.DirectivesException import DirectivesException
from sharcnet_helper.env import make_venv, find_python_version


class Directives:
    def __init__(
            self,
            mem: str,
            hours: int,
            modules: List[str],
            working_dir: Path,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None,
            email: str | None = None,
            account: str | None = None
    ):
        """
        :param mem: the memory to allocate for the job
        :param hours: the number of hours to allocate for the job
        :param minutes: the number of minutes to allocate for the job
        :param working_dir: the working directory for the job
        :param modules: the modules to load for the job
        :param job_name: the name of the job
        :param array_job: if this is an array job, the number of runs in the array
        :param mail_type: the type of email to send. ALL, BEGIN, END, FAIL, REQUEUE, TIME_LIMIT, TIME_LIMIT_90, defaults to FAIL
        :param n_tasks: the number of tasks to use per node, defaults to None
        """
        self.mem = mem
        self.hours = hours
        self.minutes = minutes
        self.working_dir = working_dir
        self.modules = modules
        self.job_name = job_name
        self.array_job = array_job
        self.mail_type = mail_type
        self.n_tasks = n_tasks
        self.email = email
        self.account = account

    def make_directives(self, *args, sep: str = "_") -> str:
        return _make_directives(self, *args, sep=sep)

    def __str__(self) -> str:
        """
        Return the directives as a string.
        """
        return _make_directives(self)


class PythonDirectives(Directives):
    def __init__(
            self,
            mem: str,
            hours: int,
            working_dir: Path,
            env_path: Path | None,
            modules: List[str] | None = None,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None,
            scipy_stack: bool = False,
            python_packages: List[str] | None = None,
            python_version: str | None = None,
            venv_name: str | None = None,
            email: str | None = None,
            account: str | None = None,
            requirements_txt: str | None = None,
            verbose: bool = False
    ):
        """
        :param env_path: The path to the Python virtual environment.
        :param scipy_stack: A flag indicating whether to include the 'scipy-stack' module.
        :param python_packages: A list of additional Python packages to install in the environment.
        """
        super().__init__(mem=mem, hours=hours, modules=modules, working_dir=working_dir, minutes=minutes,
                         job_name=job_name, array_job=array_job, mail_type=mail_type, n_tasks=n_tasks, email=email,
                         account=account)
        self.env_path = env_path
        self.scipy_stack = scipy_stack
        self.python_packages = python_packages
        self.requirements_txt = requirements_txt
        self.modules.append("scipy-stack") if self.scipy_stack else ...
        self.venv_name = venv_name if venv_name is not None else env_path.name
        self.python_version = find_python_version(python_version)
        self.modules.append(self.python_version)
        self.verbose = verbose

        make_venv(self.env_path, self.python_packages, self.python_version, self.modules, file_name=None,
                  verbose=verbose)
        self.update_packages(verbose)

    @classmethod
    def from_file(
            cls,
            mem: str,
            hours: int,
            working_dir: Path,
            file_path: Path,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None
    ):
        """
        :param file_path: Path to the configuration file in TOML format.

        :return: An initialized class instance based on the configuration.
        """
        with open(file_path, "rb") as file:
            parameters = tomllib.load(file)

        return cls(mem, hours, parameters["modules"], working_dir, parameters["env_path"], minutes, job_name, array_job,
                   mail_type, n_tasks, False, parameters["packages"])

    def update_packages(self, verbose: bool) -> None:
        """
        Update Python packages for the environment using specified modules and packages.

        :raises subprocess.SubprocessError: Raised if the subprocess encounters issues during execution.
        """
        print("Updating packages...")
        if self.python_packages is None and self.requirements_txt is None:
            return
        elif self.requirements_txt is None:
            commands = f'''
                    module load {" ".join(self.modules)}
                    source {self.env_path.absolute()}/bin/activate
                    pip install {' '.join([x for x in self.python_packages])}
                    '''
        else:
            commands = f'''
                    module load {" ".join(self.modules)}
                    source {self.env_path.absolute()}/bin/activate
                    pip install -r {self.requirements_txt}
                    pip install {' '.join([x for x in self.python_packages])}
                    '''
        process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        o, e = process.communicate(commands)
        if e is not None:
            print(e)
        if verbose:
            print(o)

    def make_directives(self, *args, sep: str = "_") -> str:
        return _make_directives(self, *args, sep=sep) + f"source {self.env_path.absolute()}/bin/activate"


def _make_directives(directives: Directives, *args, sep: str = "_") -> str:
    def array_job_fn():
        if directives.array_job is None:
            return ""
        elif type(directives.array_job) == list:
            return "#SBATCH --array=" + ",".join(str(i) for i in directives.array_job)
        else:
            return f"#SBATCH --array=1-{str(directives.array_job)}"

    def n_tasks_fn():
        if directives.n_tasks is None:
            return ""
        else:
            return f"#SBATCH --ntasks-per-node={str(directives.n_tasks)}"

    if args:
        directives.job_name = sep.join(str(arg) for arg in args)

    if not directives.mem:
        raise DirectivesException("Memory value is an empty string. You need to specify a memory value.")

    directives_text = textwrap.dedent(f'''\
                #!/bin/bash
                #SBATCH --time={str(directives.hours)}:{str(directives.minutes) if directives.minutes > 0 else "00"}:00
                #SBATCH --account={directives.account}
                #SBATCH --mem={directives.mem}
                {array_job_fn()}
                {n_tasks_fn()}
                #SBATCH --mail-user={directives.email}
                #SBATCH --mail-type={directives.mail_type if type(directives.mail_type) == str else ','.join(directives.mail_type)}
                #SBATCH --output={directives.working_dir.absolute()}/output/slurm_{"%A_%a" if directives.array_job is not None else "%j"}_{directives.job_name}.out
                #SBATCH --job-name={directives.job_name}
            ''')

    directives_text = directives_text.replace("\n\n", "\n")
    directives_text = directives_text.replace("\n\n", "\n")
    directives_text += textwrap.dedent(f'''
            mkdir -p {directives.working_dir.absolute()}/output
            module load {' '.join(directives.modules)}
        ''')

    return directives_text
