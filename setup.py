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
    packages=find_packages(),
    install_requires=[
        'python-gitlab',
    ],
    scripts=['bin/abgabesystem'],
    zip_safe=False,
    license='GPLv3')
