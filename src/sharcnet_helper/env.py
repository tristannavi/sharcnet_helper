import argparse
import subprocess
from pathlib import Path
from typing import List


def make_venv(venv_name: str, path: Path = Path.home(), packages: List[str] | None = None, version: str | None = None,
              modules2: List[str] | None = None, file_name: str | None = "") -> None:
    """
    Create a virtual environment with the given name.
    :param scipy_stack:
    :param version:
    :param packages: List of packages to install in the virtual environment.
    :param path: Path to the directory where the virtual environment will be created.
    :param venv_name: Name of the virtual environment to create.
    :return: None
    """
    # Check if the virtual environment already exists
    if not Path(venv_name).exists():
        if version is not None:
            version = find_python_version(version)
            modules = find_python_modules(version)
        else:
            version = None
            modules = None

        commands = f'''
        {"module load " + " ".join(modules) if modules is not None else ""}
        module load {version if version is not None else "python"}
        {"module load " + " ".join(modules2) if modules2 is not None else ""}
        virtualenv --no-download {path.absolute()}/{venv_name}
        source {path.absolute()}/{venv_name}/bin/activate
        pip install --upgrade pip
        pip -v install {' '.join(packages)}
        '''

        process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        process.communicate(commands)

        print(f"Virtual environment {venv_name} created with Python version {version} and modules {modules}")

        if file_name is not None:
            make_file(venv_name if file_name == "" else file_name, path, packages, modules)
    else:
        print(f"Virtual environment {venv_name} already exists")


def make_file(file_name: str, path: Path, packages: List[str] | None, modules: List[str] | None):
    with open(f"{file_name}.toml", "w") as file:
        file.writelines(f'env_path = "{path.absolute()}')
        file.writelines(f'packages = [{", ".join(packages) if packages is not None else ""}]')
        file.writelines(f'modules = [{", ".join(modules) if modules is not None else ""}]')


def find_python_version(version: str) -> str | None:
    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, err = process.communicate("module spider python")
    for line in out.split('\n'):
        if line.strip().startswith('python/'):
            if version in line:
                return line.strip()
    return None


def find_python_modules(version: str) -> List[str] | None:
    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    out, err = process.communicate(f'module spider {version}')
    modules = []

    out_generator = iter(out.splitlines())

    line = next(out_generator)
    while True:
        if 'You will need to load all module(s)' in line:
            break
        line = next(out_generator)

    line = next(out_generator)
    line = next(out_generator)
    while True:
        if line.strip() == "":
            break
        modules.append(line.strip())
        try:
            line = next(out_generator)
        except StopIteration:
            break

    return modules


def main():
    parser = argparse.ArgumentParser(description='Create a virtual environment')
    parser.add_argument('venv_name', help='Name of the virtual environment')
    parser.add_argument('--path', type=Path, default=Path.home(), help='Path to create the virtual environment')
    parser.add_argument('--packages', nargs='+', help='Packages to install in the virtual environment')
    parser.add_argument('--version', help='Python version to use')
    parser.add_argument('--modules2', nargs='+', help='Additional modules to load')

    args = parser.parse_args()

    make_venv(args.venv_name, args.path, args.packages, args.version, args.modules2)


if __name__ == '__main__':
    main()
