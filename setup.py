"""
Senthium - Intelligent Lock & Sleep Manager
Setup configuration for package installation
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
    return "Intelligent, rule-based lock and sleep manager"

setup(
    name='senthium',
    version='0.1.0',
    author='Your Name',  # TODO: Update this
    author_email='your.email@example.com',  # TODO: Update this
    description='Intelligent, rule-based lock and sleep manager',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/senthium',  # TODO: Update this
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/senthium/issues',
        'Source': 'https://github.com/yourusername/senthium',
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Power (UPS)',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
    ],
    keywords='power-management sleep lock daemon system-utility',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.9',
    install_requires=[
        'psutil>=5.9.0',
        'pyyaml>=6.0',
        'colorlog>=6.7.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.11.0',
            'black>=23.7.0',
            'flake8>=6.1.0',
            'mypy>=1.5.0',
        ],
        'linux': [
            'dbus-python>=1.3.2',
        ],
        'windows': [
            'pywin32>=306',
        ],
    },
    entry_points={
        'console_scripts': [
            'senthium=cli.wrapper:main',
            'senthiumd=daemon.core:main',
        ],
    },
)
