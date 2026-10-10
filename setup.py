from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cbpi4_BrewStart",
    version="1.0.0",
    description="CraftBeerPi4 Mash-Step: Brauvorgang zu einer geplanten Startzeit starten",
    author="CraftBeerPi Community",
    url="https://github.com/",
    include_package_data=True,
    package_data={
        "": ["*.txt", "*.rst", "*.yaml", "*.md"],
        "cbpi4_BrewStart": ["*", "*.txt", "*.rst", "*.yaml", "*.md"],
    },
    packages=["cbpi4_BrewStart"],
    install_requires=[
        "cbpi>=4.0.0.33",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Home Automation",
    ],
)