from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="discord_retriever",
    version="0.1.0",
    author="Joseph Young",
    author_email="joe@youngsecurity.net",
    description="A tool for retrieving Discord messages and storing them in a vector database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/youngsecurity-org/discord_vector_db",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "discord-retriever=discord_retriever.cli:main",
        ],
    },
)
