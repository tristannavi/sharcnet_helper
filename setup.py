from setuptools import setup, find_packages

setup(
    name='sharcnet_helper',
    version='1.0',
    url='',
    license='GPL',
    author='Tristan',
    author_email='',
    description='',
    package_dir={'': 'src'},
    packages=find_packages(
        # All keyword arguments below are optional:
        where='src',  # '.' by default
        include=['*'],  # ['*'] by default
    )
)
