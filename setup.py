"""
SftpMan GTK
===========

A GTK frontend for SftpMan, which makes it easy to setup and mount SSHFS/SFTP file systems.

It allows you to define all your SFTP systems and easily mount/unmount them.
"""

from setuptools import setup

setup(
    name = "sftpman-gtk",
    version = '0.2.0',
    description = "A GTK frontend for SftpMan, which helps you mount SFTP file systems.",
    long_description = __doc__,
    author = "Slavi Pantaleev",
    author_email = "s.pantaleev@gmail.com",
    url = "https://github.com/spantaleev/sftpman-gtk",
    keywords = ["sftp", "ssh", "sshfs", "gtk"],
    license = "BSD",
    packages = ['sftpman_gtk'],
    install_requires = ['sftpman'],
    entry_points="""
    [console_scripts]
    sftpman-gtk = sftpman_gtk.launcher:main
    """,
    zip_safe = False,
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
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
