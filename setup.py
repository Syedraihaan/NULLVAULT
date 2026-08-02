from setuptools import setup, find_packages

setup(
    name="nullvault",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography>=41.0.0",
        "bcrypt>=4.0.0",
        "click>=8.1.0",
    ],
    entry_points={
        "console_scripts": [
            "nullvault=main:cli",
        ],
    },
    python_requires=">=3.10",
)
