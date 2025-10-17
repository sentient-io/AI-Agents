from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="video-metadata-manager",
    version="0.1.0",
    author="SENTIENT.IO PTE. LTD",
    author_email="enquiry@sentient.io",
    description="A Python library for managing video metadata with MySQL",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sentient-io/video-metadata",
    packages=find_packages(),
    install_requires=[
        'PyMySQL>=1.0.2',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)