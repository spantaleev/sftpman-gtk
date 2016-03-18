import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


BOX_SPACING = 5


def open_file_browser(path):
    """Opens a file browser at the specified path."""
    import subprocess
    subprocess.Popen(["xdg-open", path])


def create_button(text, stock_image_id=None, onclick=None):
    hbox = Gtk.HBox()

    if stock_image_id is not None:
        icon = Gtk.Image()
        icon.set_from_stock(stock_image_id, Gtk.IconSize.SMALL_TOOLBAR)
        hbox.pack_start(icon, True, True, 0)

    label = Gtk.Label()
    label.set_text(text)
    label.set_alignment(0, 0)

    hbox.pack_start(label, True, True, 0)

    btn = Gtk.Button()
    btn.add(hbox)

    if onclick is not None:
        btn.connect("clicked", onclick)

    return btn


def show_warning_message(text):
    md = Gtk.MessageDialog(None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.WARNING,
        Gtk.ButtonsType.CLOSE, text)
    md.run()
    md.destroy()


def create_hbox():
    return Gtk.HBox(spacing=BOX_SPACING)


def create_vbox():
    return Gtk.VBox(spacing=BOX_SPACING)


def create_table():
    table = Gtk.Table(homogeneous=True)
    table.set_row_spacings(BOX_SPACING)
    table.set_col_spacings(BOX_SPACING)
    return table
