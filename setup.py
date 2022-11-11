from setuptools import find_packages, setup

setup(
    name="db-cli",
    version="1.0",
    packages=find_packages(exclude=['tests']),
    install_requires=[
        "pubnub",
        "textual",
        "xdg",
    ],
    entry_points={
        'console_scripts': [
            'bus=bus.__main__:main',
        ],
    },
)
