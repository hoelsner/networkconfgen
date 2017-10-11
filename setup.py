import sys
from setuptools import setup

if sys.version_info <= (3, 0):
    # py2-ipaddress backport required
    dependencies = [
        "Jinja2>=2.9.5",
        "py2-ipaddress>=3.4.1"
    ]

else:
    dependencies = [
        "Jinja2>=2.9.5"
    ]

setup(
    name="networkconfgen",
    version="0.2.0",
    description="Jinja2 based configuration generator with some extensions required to generate configurations "
                "for network devices",
    url="https://github.com/hoelsner/networkconfgen",
    author="Henry Ölsner",
    author_email="henry@codingnetworker.com",
    license="MIT",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=dependencies,
    extras_require={
        'test': ['pytest>=3.0.6', 'tox>=2.7.0']
    },
    packages=[
        "networkconfgen"
    ]
)
