import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


BOX_SPACING = 5
ROW_SPACING = 15

def open_file_browser(path):
    """Opens a file browser at the specified path."""
    import subprocess
    subprocess.Popen(["xdg-open", path])


def show_warning_message(parent_window, text):
    md = Gtk.MessageDialog(parent_window, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING,
        Gtk.ButtonsType.CLOSE, text)
    md.run()
    md.destroy()


def create_hbox():
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=BOX_SPACING)


def create_vbox():
    return Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=BOX_SPACING)


def create_table():
    table = Gtk.Table(homogeneous=True)
    table.set_row_spacings(ROW_SPACING)
    table.set_col_spacings(BOX_SPACING)
    table.set_margin_top(ROW_SPACING)
    return table
