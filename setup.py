from setuptools import setup, find_packages

setup(
    name="openthought",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
    ],
    extras_require={
        "all": [
            "click>=8.0.0",
            "openai>=1.0.0",
            "pytest>=7.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openthought=openthought.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Agent_Li",
    author_email="jh_li07@outlook.com",
    description="A chain-of-thought tool for deep reflection",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jhli07/OpenThought",
    project_urls={
        "Bug Reports": "https://github.com/jhli07/OpenThought/issues",
        "Source": "https://github.com/jhli07/OpenThought",
        "Documentation": "https://github.com/jhli07/OpenThought#readme",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="thinking, reflection, socratic, chain-of-thought, ai-tool",
)
