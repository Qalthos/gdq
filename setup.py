from setuptools import setup, find_packages


setup(
    name="gdq-cli",
    version=1.0,
    packages=find_packages(exclude=['tests']),
    install_requires=[
        "python-dateutil",
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
