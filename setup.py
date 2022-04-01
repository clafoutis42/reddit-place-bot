import re
from os.path import abspath, dirname, join

from setuptools import setup

VERSION_RE = re.compile(r"__version__\s*=\s*\"(.*?)\"")
PACKAGE_NAME = "reddit-place-bot"

current_path = abspath(dirname(__file__))

with open(join(current_path, PACKAGE_NAME, "__init__.py")) as file:
    result = VERSION_RE.search(file.read())
    if result is None:
        raise Exception("could not find package version")
    __version__ = result.group(1)

setup(
    name=PACKAGE_NAME,
    description="App that allows admins to create channels for their campus.",
    author="Charles Labourier",
    author_email="charles@clabouri.dev",
    version=__version__,
    packages=["redditplacebot"],
    install_requires=[
        "requests",
    ],
    zip_safe=True,
)
