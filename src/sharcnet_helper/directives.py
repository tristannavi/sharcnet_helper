import textwrap
import tomllib
from pathlib import Path
from typing import List


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
            *args
    ):
        """
        :param mem: the memory to allocate for the job
        :type mem: str, required
        :param hours: the number of hours to allocate for the job
        :type hours: int, required
        :param minutes: the number of minutes to allocate for the job
        :type minutes: int, optional
        :param working_dir: the working directory for the job
        :type working_dir: Path, required
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
                    #SBATCH --output={self.working_dir.absolute()}/output/slurm_{self.job_name}-{"%A_%a" if self.array_job is not None else "%j"}.out
                    #SBATCH --job-name={self.job_name}-{"%A_%a" if self.array_job is not None else "%j"}
                ''')

        directives.replace("\n\n", "\n")
        directives += textwrap.dedent(f'''
                mkdir -p {self.working_dir.absolute()}/output
                module load {' '.join(self.modules)}
            ''')

        return directives

    def __str__(self) -> str:
        """
        Return the directives as a string.
        :rtype: str
        """
        return self.make_directives()


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
            python_packages: List[str] | None = None,
            *args
    ):
        super().__init__(mem, hours, modules, working_dir, minutes, job_name, array_job, mail_type, n_tasks, *args)
        self.env_path = env_path
        self.scipy_stack = scipy_stack
        self.python_packages = python_packages
        self.modules.append("python")
        self.modules.append("scipy-stack") if self.scipy_stack else ...

    @classmethod
    def from_file(
            cls,
            mem: str,
            hours: int,
            modules: List[str],
            working_dir: Path,
            file_path: Path,
            minutes: int = 0,
            job_name: str | None = None,
            array_job: int | List[int] | None = None,
            mail_type: str | List[str] | None = "FAIL",
            n_tasks: int | None = None,
            *args,
    ):
        with open(file_path, "rb") as file:
            parameters = tomllib.load(file)

        return cls(mem, hours, parameters["modules"], working_dir, parameters["env_path"], minutes, job_name, array_job,
                   mail_type,
                   n_tasks, False, parameters["packages"], *args)

    def __call__(self):
        commands = f'''
                module load {" ".join(self.modules)}
                source {self.env_path.absolute()}/bin/activate
                pip install --force-reinstall -v {' '.join(packages)}
                '''
        process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        process.communicate(commands)
        # return super().make_directives() + textwrap.dedent(f'''
        #         source {self.env_path.absolute()}/bin/activate
        #     ''')
