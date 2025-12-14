from setuptools import setup, find_packages

setup(
    name="mlops-breast-cancer",
    version="0.0.0",
    description="Minimal package wrapper for editable install",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
