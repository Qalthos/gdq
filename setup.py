from setuptools import find_packages, setup

setup(
    name="gdq-cli",
    version=1.0,
    packages=find_packages(exclude=['tests']),
    install_requires=[
        "requests",
        "toml",
        "xdg",
    ],
    entry_points={
        'console_scripts': [
            'gdq=gdq.__main__:main',
        ],
    },
)
