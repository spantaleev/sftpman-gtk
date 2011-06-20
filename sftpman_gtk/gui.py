import os
from threading import Thread
from time import sleep

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from sftpman.model import EnvironmentModel, SystemModel, SystemControllerModel
from sftpman.exception import SftpException, SftpMountException
from sftpman.helper import shell_exec

from helper import open_file_browser, create_button, show_warning_message


class SftpManGtk(object):

    def handler_destroy(self, widget, data=None):
        gtk.main_quit()

    def destroy(self, widget, data=None):
        gtk.main_quit()

    def _get_system_by_id(self, system_id):
        return SystemModel.create_by_id(system_id, self.environment)

    def _get_system_controller_by_id(self, system_id):
        system =  SystemModel.create_by_id(system_id, self.environment)
        return SystemControllerModel(system, self.environment)

    def handler_open_by_id(self, btn, system_id):
        controller = self._get_system_controller_by_id(system_id)
        if controller.mounted:
            open_file_browser(controller.mount_point_local)

    def _handle_mount(self, system_id):
        controller = self._get_system_controller_by_id(system_id)
        try:
            controller.mount()
        except SftpMountException, e:
            msg = ('Mounting failed for {system_id}.\n\n'
                   'Mount command:\n{cmd}\n\n'
                   'Command output:\n{output}')
            msg = msg.format(
                system_id = system_id,
                cmd = e.mount_cmd,
                output = e.mount_cmd_output,
            )
            show_warning_message(msg)

    def handler_mount_by_id(self, btn, system_id):
        self._handle_mount(system_id)
        self.refresh_list()

    def handler_unmount_by_id(self, btn, system_id):
        controller = self._get_system_controller_by_id(system_id)
        controller.unmount()
        self.refresh_list()

    def handler_mount_all(self, btn):
        for system_id in self.environment.get_available_ids():
            self._handle_mount(system_id)
        self.refresh_list()

    def handler_unmount_all(self, btn):
        for system_id in self.environment.get_mounted_ids():
            controller = self._get_system_controller_by_id(system_id)
            controller.unmount()
        self.refresh_list()

    def handler_create_new(self, btn):
        system = SystemModel()
        system.id = ''
        system.user = shell_exec('whoami').strip()
        system.mount_point = '/home/%s/' % system.user
        system.mount_opts = ['follow_symlinks', 'workaround=rename', 'big_writes']
        RecordRenderer(self, system, added=False).render()

    def handler_edit(self, btn, system_id):
        system = self._get_system_by_id(system_id)
        RecordRenderer(self, system, added=True).render()

    def refresh_list(self):
        ids_mounted = self.environment.get_mounted_ids()

        for childHbox in self.list_container.get_children():
            self.list_container.remove(childHbox)

        separator = gtk.HBox()
        separator.set_size_request(10, 25)
        self.list_container.pack_start(separator, False)

        ids_available = self.environment.get_available_ids()
        for system_id in ids_available:
            is_mounted = system_id in ids_mounted

            hbox = gtk.HBox()

            icon = gtk.Image()
            icon.set_from_stock(gtk.STOCK_YES if is_mounted else gtk.STOCK_NO, gtk.ICON_SIZE_SMALL_TOOLBAR)
            hbox.pack_start(icon)

            # Sftp system id
            label = gtk.Label(system_id)
            label.set_alignment(0, 0)
            label.set_size_request(150, 35)
            hbox.pack_start(label)

            # Open/Mount button
            if (is_mounted):
                btn_mount_or_open = create_button('Open', gtk.STOCK_OPEN)
                btn_mount_or_open.connect('clicked', self.handler_open_by_id, system_id)
            else:
                btn_mount_or_open = create_button('Mount', gtk.STOCK_CONNECT)
                btn_mount_or_open.connect('clicked', self.handler_mount_by_id, system_id)

            # Unmount button
            btn_unmount = create_button('Unmount', gtk.STOCK_DISCONNECT)
            if (not is_mounted):
                btn_unmount.set_sensitive(False)
            else:
                btn_unmount.connect('clicked', self.handler_unmount_by_id, system_id)

            # Edit button
            btn_edit = create_button('Edit', gtk.STOCK_EDIT)
            btn_edit.connect('clicked', self.handler_edit, system_id)

            hbox.pack_start(btn_mount_or_open)
            hbox.pack_start(btn_unmount)
            hbox.pack_start(btn_edit)

            self.list_container.pack_start(hbox, False)

        if len(ids_available) == 0:
            label = gtk.Label()
            label.set_text('No sftp systems added yet.')
            label.set_justify(gtk.JUSTIFY_CENTER)
            self.list_container.pack_start(label)

        self.list_container.show_all()

    def _create_tool_box(self):
        hbox = gtk.HBox()
        hbox.pack_start(create_button('New', gtk.STOCK_ADD, onclick=self.handler_create_new))
        hbox.pack_start(create_button('Mount all', gtk.STOCK_CONNECT, onclick=self.handler_mount_all))
        hbox.pack_start(create_button('Unmount all', gtk.STOCK_CONNECT, onclick=self.handler_unmount_all))
        return hbox

    def _create_list_container(self):
        # This would contain the sftp systems list
        self.list_container = gtk.VBox()
        self.refresh_list()
        return self.list_container

    def _create_record_container(self):
        # This would contain the form entries when adding/editing systems
        self.record_container = gtk.HBox()
        return self.record_container

    def __init__(self):
        self.environment = EnvironmentModel()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title('SftpMan')
        self.window.resize(550, 350)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.connect('destroy', self.handler_destroy)

        icon_file = os.path.join(os.path.dirname(__file__), '..', 'sftpman.png')
        if not os.path.exists(icon_file):
            icon_file = '/usr/share/pixmaps/sftpman.png'
            if not os.path.exists(icon_file):
                icon_file = None
        if icon_file is not None:
            self.window.set_icon_from_file(icon_file)

        vbox_main = gtk.VBox()
        vbox_main.pack_start(self._create_tool_box(), False)
        vbox_main.pack_start(self._create_list_container())
        vbox_main.pack_start(self._create_record_container())

        self.window.add(vbox_main)
        self.window.show_all()

        self.in_list_mode = True

        # we need to do this if we want to use threads in our GTK app
        gobject.threads_init()

        def list_periodic_refresher():
            while True:
                # Trying to update the GTK GUI from a thread causes
                # a segmentation fault - this is the proper way to do it
                if self.in_list_mode:
                    gobject.idle_add(self.refresh_list)
                sleep(15)

        refresher_thread = Thread(target=list_periodic_refresher)
        refresher_thread.daemon = True
        refresher_thread.start()

    def _perform_preflight_check(self):
        checks_pass, failures = self.environment.perform_preflight_check()
        if not checks_pass:
            for msg in failures:
                show_warning_message(msg)
            show_warning_message('Mounting will fail until all problems are fixed.')

    def main(self):
        self._perform_preflight_check()
        gtk.main()


class RecordRenderer(object):
    """Deals with the record form (Adding/Editing sftp systems)."""

    def __init__(self, window_obj, system, added):
        self.window_obj = window_obj
        self.environment = self.window_obj.environment
        self.system = system
        self.added = added

        self.window_obj.list_container.hide()
        self.window_obj.in_list_mode = False

    def get_fields(self):
        return (
            {'id': 'id', 'type': 'textbox', 'title': 'Machine Id/Name', 'disabled': self.added},
            {'id': 'host', 'type': 'textbox', 'title': 'Host', 'disabled': False},
            {'id': 'port', 'type': 'textbox', 'title': 'Port', 'disabled': False},
            {'id': 'user', 'type': 'textbox', 'title': 'Username', 'disabled': False},
            {'id': 'ssh_key', 'type': 'filepath', 'title': 'SSH key', 'disabled': False},
            {'id': 'mount_point', 'type': 'textbox', 'title': 'Remote mount point', 'disabled': False},
            {'id': 'mount_opts', 'type': 'options', 'title': 'Options', 'disabled': False},
            {'id': 'cmd_before_mount', 'type': 'textbox', 'title': 'Run before mount', 'disabled': False},
        )

    def get_field_value(self, field_name):
        value = getattr(self.system, field_name, None)
        return value if value is not None else ''

    def render_textbox(self, field_info):
        textbox = gtk.Entry()
        textbox.set_text(str(self.get_field_value(field_info['id'])))
        textbox.set_size_request(250, 25)
        if field_info.get('disabled', False):
            textbox.set_sensitive(False)
        return textbox

    def get_value_textbox(self, widget):
        return widget.get_text()

    def render_filepath(self, field_info):
        path_now = self.get_field_value(field_info['id'])

        textbox = gtk.Entry()
        textbox.set_text(path_now)

        def filechooser_start(btn):
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
            filechooser = gtk.FileChooserDialog('Select your private ssh key file:', None, gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
            if os.path.exists(path_now):
                start_path = os.path.dirname(path_now)
            else:
                home_path = os.path.expanduser('~')
                ssh_path = '%s/.ssh/' % home_path
                start_path = ssh_path if os.path.exists(ssh_path) else home_path
            filechooser.set_current_folder(start_path)

            if filechooser.run() == gtk.RESPONSE_OK:
                textbox.set_text(filechooser.get_filename())

            filechooser.destroy()

        btn_browse = create_button('..', onclick=filechooser_start)
        btn_browse.set_size_request(20, 25)

        hbox = gtk.HBox()
        hbox.pack_start(textbox)
        hbox.pack_start(btn_browse, False)
        hbox.set_size_request(250, 25)

        return hbox

    def get_value_filepath(self, widget):
        textbox = widget.get_children()[0]
        return textbox.get_text()

    def render_options(self, field_info):
        options = self.get_field_value(field_info['id'])
        textbox = gtk.Entry()
        textbox.set_text(', '.join(options))
        textbox.set_size_request(250, 25)
        return textbox

    def get_value_options(self, widget):
        return [option.strip() for option in widget.get_text().split(',')]

    def handler_save(self, btn, fields):
        if not self.added:
            controller = None
            is_mounted_before_save = False
        else:
            controller = SystemControllerModel(self.system, self.environment)
            is_mounted_before_save = controller.mounted
            controller.unmount()

        for field_info in fields:
            widget = field_info['widget']

            get_value_callback = getattr(self, 'get_value_%s' % field_info['type'], None)
            if get_value_callback is None:
                raise SftpException('Cannot get value for field type: %s' % field_info['type'])
            value = get_value_callback(widget)
            setattr(self.system, field_info['id'], value)

        is_valid, errors = self.system.validate()
        if is_valid:
            self.system.save(self.environment)

            if is_mounted_before_save:
                controller.mount()

            self.close()
        else:
            for field_id, msg in errors:
                show_warning_message(msg)

    def handler_delete(self, btn):
        dialog = gtk.MessageDialog(self.window_obj.window, gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, 'Are you sure?')
        dialog.set_title('Delete %s?' % self.system.id)
        dialog.show()

        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_YES:
            controller = SystemControllerModel(self.system, self.environment)
            controller.unmount()
            self.system.delete(self.environment)
            self.close()

    def handler_cancel(self, btn):
        self.close()

    def close(self):
        # Get rid of all the fields we rendered in the record container,
        # but preserve the container for later use
        for child in self.window_obj.record_container.get_children():
            self.window_obj.record_container.remove(child)
        self.window_obj.refresh_list()
        self.window_obj.list_container.show()
        self.window_obj.in_list_mode = True

    def render(self):
        for child in self.window_obj.record_container.get_children():
            self.window_obj.record_container.remove(child)

        vbox = gtk.VBox()

        title = gtk.Label()
        title_label = 'System editing' if self.added else 'System adding'
        title.set_markup('<big>%s</big>' % title_label)
        vbox.pack_start(title)
        vbox.pack_start(gtk.HSeparator())

        fields = []
        for field_info in self.get_fields():
            hbox = gtk.HBox()

            label = gtk.Label()
            label.set_text(field_info['title'])
            label.set_alignment(0, 0)
            label.set_size_request(80, 20)

            hbox.pack_start(label)

            render_callback = getattr(self, 'render_%s' % field_info['type'], None)
            if render_callback is None:
                raise SftpException('Missing renderer for field type %s' % field_info['type'])

            widget = render_callback(field_info)

            field_info['widget'] = widget

            hbox.pack_start(widget)

            vbox.add(hbox)

            fields.append(field_info)

        # Form actions (Save, Delete, etc..)
        hbox = gtk.HBox()
        hbox.set_size_request(width=-1, height=25)

        btn_save = create_button('Save', gtk.STOCK_SAVE)
        btn_save.connect('clicked', self.handler_save, fields)
        hbox.pack_start(btn_save)

        btn_cancel = create_button('Cancel', gtk.STOCK_CANCEL, onclick=self.handler_cancel)
        hbox.pack_start(btn_cancel)

        if self.added:
            btn_delete = create_button('Delete', gtk.STOCK_DELETE, onclick=self.handler_delete)
            hbox.pack_start(btn_delete)

        vbox.add(hbox)

        self.window_obj.record_container.add(vbox)
        self.window_obj.record_container.show_all()

        if not self.added:
            # Give focus to the first field in the form
            fields[0]['widget'].grab_focus()


def start():
    obj = SftpManGtk()
    obj.main()
