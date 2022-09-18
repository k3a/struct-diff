from setuptools import setup, find_packages

version_string = __import__('struct_diff').__version__

setup(
    name='struct-diff',
    version=version_string,
    description='Structural comparison of two objects.',
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/k3a/struct_diff',
    author='K3A',
    license='MIT',
    clasifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"
    ],
    package_dir={'struct_diff': 'struct_diff', 'tests': 'tests'},
    packages=find_packages(),
)
