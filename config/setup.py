from setuptools import setup, find_packages

setup(
    name="FolderMonitoringApp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "watchdog==6.0.0",
        "requests==2.32.3",
        "urllib3==2.3.0",
        "PyYAML==5.4.1",
    ],
    entry_points={
        "console_scripts": [
            "folder_monitor=FolderUpdates.main:main",
        ],
    },
    author="graybiralo",
    description="A folder monitoring application that notifies connected clients of changes.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
