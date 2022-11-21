from setuptools import find_packages, setup

setup(
    name="gdq-cli",
    version="2.0",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "pubnub",
        "requests",
        "xdg",
    ],
    entry_points={
        "console_scripts": [
            "bus=bus.__main__:main",
            "gdq=gdq.__main__:main",
        ],
    },
)
