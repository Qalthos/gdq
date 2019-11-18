from setuptools import setup, find_packages


setup(
    name="gdq-cli",
    version=0.9,
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'gdq=gdq.board:main',
            'bus=gdq.bus:main',
        ],
    },
)
