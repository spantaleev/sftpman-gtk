SftpMan GTK
===========

.. image:: https://github.com/spantaleev/sftpman-gtk/raw/master/sftpman-gui.png

---------------------------------------

SftpMan consists of a Command Line and a GTK application that make it simpler to setup and mount SSHFS/SFTP file systems.

The idea was to develop a simple CLI/GUI application for Linux that can be used to manage SFTP file systems.

It relies on `sshfs`_ to do all the mounting work.
SftpMan allows you to setup many remote filesystems and helps you easily mount/unmount them.

Every system managed by SftpMan is identified by an id such as ``my-machine``, which is used in file paths and when managing the system.

Configuration data is stored in ``~/.config/sftpman/`` as JSON files.

All systems are mounted under ``/mnt/sshfs/``. For the ``my-machine`` machine, that would be ``/mnt/sshfs/my-machine``.

---------------------------------------


Installing on ArchLinux
-----------------------

On `ArchLinux`_, there's an official `sftpman-gtk AUR package`_. To install using `yaourt`_::

    yaourt -S sftpman-gtk

The package takes care of all dependencies and SftpMan should be able to start.

Optional dependencies will be suggested to you upon install.


Installing on other distributions
---------------------------------

For other distributions you can install from `PyPI`_ using `pip`_::

    pip install sftpman-gtk

You'll need to install ``pygobject`` manually, but most probably you already have it installed.
Installing ``pygobject`` from **PyPI** is not supported.
If you don't have it installed, try to look for it in your distribution's package manager.

You also need to install `sshfs`_ yourself.


Post-installation tips
----------------------

If you're authenticating using passwords or password-protected SSH keys
and you want the GUI Application to prompt you for those passwords,
you may need to install the `openssh-askpass` package (or whatever it's called) for your distribution.
Some distributions have that installed by default.


GUI (GTK) Application
---------------------

In order to setup an sftp system for further use (mounting/unmounting) you need to specify:

- Hostname/IP
- Port (defaults to 22)
- Username to authenticate with
- Authentication method (using passwords or public keys)
- SSH private key (if you're authenticating using SSH keys. You will also need its corresponding public key added to the remote user's .authorized_keys file)
- Remote mount point (the remote directory you want mounted on your system)
- Options (options to pass to sshfs if you want something more advanced)
- Run before mount (a command to execute before mounting)

If you're using password-based authentication or a password-protected key, you'll be asked for the password at the time of mounting.

The "Run before mount" command allows you to do whatever init stuff you want.
I'm using it to initialize my ssh-agent (by adding my key there), so that I only have to type in the key password once.


CLI Application
---------------

The ``sftpman`` executable launches the CLI application.
To learn more about it, see `sftpman`_.

Installing this GTK frontend, automatically installs the CLI application for you.


Dependencies
------------

- `sshfs`_
- Python 2.7+
- `PyGObject`_ (for Python 2.x or Python 3.x)
- GTK3
- `sftpman`_


Known limitations
-----------------

- Doesn't support mounting in a location different than ``/mnt/sshfs/``
- All logic runs in the GUI thread, which can make the GUI freeze for a while


.. _sshfs: http://fuse.sourceforge.net/sshfs.html
.. _ArchLinux: http://www.archlinux.org/
.. _AUR: https://wiki.archlinux.org/index.php/AUR
.. _sftpman-gtk AUR package: https://aur.archlinux.org/packages/sftpman-gtk/
.. _sftpman: https://github.com/spantaleev/sftpman/
.. _PyGObject: https://live.gnome.org/PyGObject
.. _pip: http://guide.python-distribute.org/pip.html
.. _PyPI: http://pypi.python.org/pypi
.. _yaourt: https://wiki.archlinux.org/index.php/Yaourt
