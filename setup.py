from setuptools import setup, find_packages

setup(
    name="alvz-lang",
    version="0.13.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "alvz=alvz:main",
            "alvz-lsp=alvz.lsp.server:main",
            "alvz-dap=alvz.lsp.dap:main",
        ],
    },
    author="Eder Alvarez",
    description="Un lenguaje de programacion con sintaxis en espanol basado en Python",
    python_requires=">=3.6",
)
