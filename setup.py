#!/usr/bin/env python3
"""
Setup script for Senthium AI
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = []

setup(
    name='senthium-ai',
    version='1.0.0',
    description='Intelligent task-aware lock system using ANN and Fuzzy Logic',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Senthium AI Contributors',
    author_email='',
    url='https://github.com/shivadeepak99/senthium-ai',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'senthium-ai=senthium_ai.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: System :: Monitoring',
        'Topic :: Security',
    ],
    keywords='lock system security ai machine-learning fuzzy-logic process-monitoring',
)
