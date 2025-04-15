import setuptools
import os

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="chait",
    version="0.1.0",
    author="Qichen",
    author_email="your_email@example.com", # Replace with your email
    description="A simple AI chat wrapper application",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/chAIt", # Replace with your repo URL if available
    packages=["chait"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License", # Choose an appropriate license
        "Operating System :: OS Independent",
    ],
    install_requires=requirements,
    python_requires='>=3.7',
    entry_points={
        'gui_scripts': [
            'chait = chait.__main__:main',
        ],
    },
    package_data={
        'chait': ['assets/icon.png', 'styles/style.css'],
    },
    include_package_data=True,
)
