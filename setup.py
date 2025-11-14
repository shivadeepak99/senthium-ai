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
    version='1.0.0',
    author='Shanigaram Shivadeepak',
    author_email='shivadeepak.dev@gmail.com',
    description='Privacy-first AI face recognition security system for monitoring unattended tasks',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/shivadeepak99/senthium-ai',
    project_urls={
        'Bug Reports': 'https://github.com/shivadeepak99/senthium-ai/issues',
        'Source': 'https://github.com/shivadeepak99/senthium-ai',
        'Documentation': 'https://github.com/shivadeepak99/senthium-ai#readme',
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Security',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Natural Language :: English',
        'Environment :: Console',
        'Environment :: Web Environment',
    ],
    keywords='security face-recognition ai deep-learning computer-vision opencv streamlit biometrics privacy localhost monitoring',
    packages=find_packages(exclude=['tests', 'tests.*', 'logs', 'logs.*', 'temp*', 'data.faces']),
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
            'senthium=src.daemon.core:main',
            'senthium-daemon=src.daemon.core:main',
            'senthium-gui=src.cli.gui:launch_gui',
        ],
    },
    include_package_data=True,
)

