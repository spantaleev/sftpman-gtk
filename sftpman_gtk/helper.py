import gtk

def open_file_browser(path):
    """Opens a file browser at the specified path."""
    import subprocess
    subprocess.Popen(["xdg-open", path])


def create_button(text, stock_image_id=None, onclick=None):
    hbox = gtk.HBox()

    if stock_image_id is not None:
        icon = gtk.Image()
        icon.set_from_stock(stock_image_id, gtk.ICON_SIZE_SMALL_TOOLBAR)
        hbox.pack_start(icon)

    label = gtk.Label()
    label.set_text(text)
    label.set_alignment(0, 0)

    hbox.pack_start(label)

    btn = gtk.Button()
    btn.add(hbox)

    if onclick is not None:
        btn.connect("clicked", onclick)

    return btn


def show_warning_message(text):
    md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_WARNING,
        gtk.BUTTONS_CLOSE, text)
    md.run()
    md.destroy()

