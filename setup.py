import os
from setuptools import setup, find_packages

setup(
    name="Homework Agent",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
        # For example:
        # "requests>=2.25.1",
        # "numpy>=1.19.2",
    ],
    author="Zhiyuan Zhang (John Zhang)",
    author_email="zhiyuan.zhang0206@gmail.com",
    description="An multi-agent system for homework completion.",
    long_description=open("readme.md").read() if os.path.exists("readme.md") else "",
    long_description_content_type="text/markdown",
)