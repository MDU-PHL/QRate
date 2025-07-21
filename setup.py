from setuptools import setup, find_packages

setup(
    name="QRate",
    version="0.1.0",
    description="A QC data curation tool for bacterial genomics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Himal Shrestha",
    author_email="himal.shrestha@unimelb.edu.au",
    url="https://github.com/MDU-PHL/QCheck",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'qrate': ['config/*.yaml'],
    },
    install_requires=[
        "PyYAML>=6.0",
    ],
    entry_points={
        'console_scripts': [
            'qrate=qrate.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.8",
)
