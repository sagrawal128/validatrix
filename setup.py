from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

with open("requirements.txt", 'r') as f:
    requires = f.read()


setup(
    name='validatrix',
    version='0.1.0',
    description='Validates data against a set of rules',
    license="MIT",
    long_description=long_description,
    author='Shubham Agrawal',
    author_email='agrawal.shubham1729@gmail.com',
    packages=['validatrix'],
    python_requires=">3.8,<3.11",
    install_requires=requires
)
