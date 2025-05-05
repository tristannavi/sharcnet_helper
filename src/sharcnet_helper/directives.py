import subprocess
import textwrap
import tomllib
from pathlib import Path
from typing import List

from sharcnet_helper.DirectivesException import DirectivesException


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
            n_tasks: int | None = None
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

    def _make_directives(self, *args, sep: str = "_") -> str:
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

        if args:
            self.job_name = sep.join(str(arg) for arg in args)

        if not self.mem:
            raise DirectivesException("Memory value is an empty string. You need to specify a memory value.")

        directives = textwrap.dedent(f'''\
                    #!/bin/bash
                    #SBATCH --time={str(self.hours)}:{str(self.minutes) if self.minutes > 0 else "00"}:00
                    #SBATCH --account=def-houghten
                    #SBATCH --mem={self.mem}
                    {array_job_fn()}
                    {n_tasks_fn()}
                    #SBATCH --mail-user=tn13bm@brocku.ca
                    #SBATCH --mail-type={self.mail_type if type(self.mail_type) == str else ','.join(self.mail_type)}
                    #SBATCH --output={self.working_dir.absolute()}/output/slurm_{"%A_%a" if self.array_job is not None else "%j"}_{self.job_name}.out
                    #SBATCH --job-name={self.job_name}_{"%A_%a" if self.array_job is not None else "%j"}
                ''')

        directives = directives.replace("\n\n", "\n")
        directives = directives.replace("\n\n", "\n")
        directives += textwrap.dedent(f'''
                mkdir -p {self.working_dir.absolute()}/output
                module load {' '.join(self.modules)}
            ''')

        return directives

    def __str__(self) -> str:
        """
        Return the directives as a string.
        """
        return self._make_directives()


class PythonDirectives(Directives):
    def __init__(
            self,
            mem: str,
            hours: int,
            modules: List[str],
            working_dir: Path,
            env_path: Path | None,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None,
            scipy_stack: bool = False,
            python_packages: List[str] | None = None
    ):
        """
        :param env_path: The path to the Python virtual environment.
        :param scipy_stack: A flag indicating whether to include the 'scipy-stack' module.
        :param python_packages: A list of additional Python packages to install in the environment.
        """
        super().__init__(mem, hours, modules, working_dir, minutes, job_name, array_job, mail_type, n_tasks)
        self.env_path = env_path
        self.scipy_stack = scipy_stack
        self.python_packages = python_packages
        self.modules.append("python")
        self.modules.append("scipy-stack") if self.scipy_stack else ...

        self.update_packages()

        # make_venv()

    @classmethod
    def new_env(
            cls,
            mem: str,
            hours: int,
            modules: List[str],
            working_dir: Path,
            env_path: Path | None,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None,
            scipy_stack: bool = False,
            python_packages: List[str] | None = None,
            python_version: str | None = None,
            venv_name: str = ""
    ):
        """
        :param python_version: Specific Python version for the virtual environment, if required.
        :param venv_name: Name for the virtual environment to be created.

        :return: A new instance of the class configured with the specified options.
        """
        cls.env_path = env_path
        cls.python_version = python_version
        cls.venv_name = venv_name

        # make_venv(venv_name, env_path, python_packages, python_version, modules)

        return cls(mem, hours, modules, working_dir, env_path, minutes, job_name, array_job,
                   mail_type, n_tasks, False, python_packages)

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

    def update_packages(self) -> None:
        """
        Update Python packages for the environment using specified modules and packages.

        :raises subprocess.SubprocessError: Raised if the subprocess encounters issues during execution.
        """
        commands = f'''
                module load {" ".join(self.modules)}
                source {self.env_path.absolute()}/bin/activate
                pip install --force-reinstall -v {' '.join([x for x in self.python_packages if "git+" in x])}
                '''
        process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        o = process.communicate(commands)
        print(o)
        # return super().make_directives() + textwrap.dedent(f'''
        #         source {self.env_path.absolute()}/bin/activate
        #     ''')
