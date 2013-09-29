"""
SftpMan GTK
===========

A GTK frontend for SftpMan, which makes it easy to setup and mount SSHFS/SFTP file systems.

It allows you to define all your SFTP systems and easily mount/unmount them.
"""

from setuptools import setup

import sftpman_gtk

setup(
    name = "sftpman-gtk",
    version = sftpman_gtk.__version__,
    description = "A GTK frontend for SftpMan, which helps you mount SFTP file systems.",
    long_description = __doc__,
    author = sftpman_gtk.__author__,
    author_email = sftpman_gtk.__author_email__,
    url = sftpman_gtk.__website_url__,
    keywords = ["sftp", "ssh", "sshfs", "gtk"],
    license = sftpman_gtk.__license__,
    packages = ['sftpman_gtk'],
    install_requires = ['sftpman>=0.5.0'],
    entry_points="""
    [console_scripts]
    sftpman-gtk = sftpman_gtk.launcher:main
    """,
    zip_safe = False,
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 5 - Production/Stable",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Topic :: Communications :: File Sharing",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Internet",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: System :: Networking",
        "Topic :: Utilities"
    ]
)
