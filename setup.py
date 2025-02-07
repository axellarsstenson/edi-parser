from setuptools import setup, find_packages

setup(
    name="edi-parser",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'edi-parser=edi_parser.parser:main',
        ],
    },
    include_package_data=True,
    author="Axel Stenson",
    author_email="axellarstenson@gmail.com",
    description="A tool for parsing EDI claims files to JSON",
    keywords="EDI, healthcare, claims, JSON parser",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/axellarsstenson/edi-parser",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license="MIT",
    python_requires=">=3.10",
)