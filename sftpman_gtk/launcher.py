#!/usr/bin/python

# launcher.main() is called by the sftpman-gtk executable (look at setup.py)
def main():
    import sys, os
    path = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, path)
    from sftpman_gtk import gui
    gui.start()

if __name__ == '__main__':
    main()
