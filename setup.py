from setuptools import setup, find_packages

setup(
    name='abgabesystem',
    version='1.0',
    description='Set up gitlab projects for coursework and plagiarism checker.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://ips1.ibr.cs.tu-bs.de/abgabesystem/abgabesystem',
    author='Tim Schubert',
    author_email='abgabesystem@timschubert.net',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'python-gitlab>=1.5.1',
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    scripts=['src/bin/abgabesystem'],
    zip_safe=False,
    license='GPLv3')
