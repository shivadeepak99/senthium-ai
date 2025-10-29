"""
Senthium AI - Face Recognition Security System
Setup configuration for pip installation
"""

try:
    from setuptools import setup, find_packages
except ImportError:
    raise ImportError(
        "setuptools is required. Install it with: pip install setuptools"
    )
import os

# Read long description from README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AI-powered face recognition security system with wake-lock protection"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            reqs = f.read().splitlines()
            return [r.strip() for r in reqs if r.strip() and not r.startswith("#")]
    return []

setup(
    name='senthium-ai',
    version='0.6.0',
    author='Senthium Team',
    author_email='contact@senthium.ai',
    description='AI-powered face recognition security system with wake-lock protection',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/senthium-ai-modern',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/senthium-ai-modern/issues',
        'Source': 'https://github.com/yourusername/senthium-ai-modern',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Security',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
    ],
    keywords='security face-recognition ai computer-vision opencv streamlit wake-lock',
    packages=find_packages(exclude=['tests', 'tests.*', 'logs', 'logs.*', 'temp*']),
    python_requires='>=3.11',
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'senthium=src.cli.main:main',
        ],
    },
    include_package_data=True,
)

