import os
from threading import Thread
from time import sleep

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gdk, GdkPixbuf

import sftpman_gtk

from sftpman.model import EnvironmentModel, SystemModel, SystemControllerModel
from sftpman.exception import SftpException, SftpMountException, SftpConfigException
from sftpman.helper import shell_exec

from .helper import open_file_browser, show_warning_message, \
     create_hbox, create_vbox, create_grid


class SftpManGtk(object):

    def handler_destroy(self, widget, data=None):
        Gtk.main_quit()

    def destroy(self, widget, data=None):
        Gtk.main_quit()

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
        except SftpMountException as e:
            msg = ('Mounting failed for {system_id}.\n\n'
                   'Mount command:\n{cmd}\n\n'
                   'Command output:\n{output}')
            msg = msg.format(
                system_id = system_id,
                cmd = e.mount_cmd,
                output = e.mount_cmd_output,
            )
            show_warning_message(self.window, msg)

    def handler_mount_by_id(self, system_id):
        self._handle_mount(system_id)
        self.refresh_list()

    def handler_unmount_by_id(self, system_id):
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

    def handler_toggle_search(self, btn):
        if self.search_bar.get_search_mode():
            # Search mode will be disabled. Clear the filter.
            self.list_filter_text = None

        self.search_bar.set_search_mode(self.btn_mount_search.get_active())

        self.refresh_list()

    def handler_about(self, btn):
        dialog = Gtk.AboutDialog()
        dialog.set_program_name('SftpMan')
        dialog.set_version(sftpman_gtk.__version__)
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.set_comments('Mount sftp/sshfs file systems with ease')
        dialog.set_website(sftpman_gtk.__website_url__)
        dialog.set_website_label(sftpman_gtk.__website_url__)
        dialog.set_copyright(sftpman_gtk.__copyright__)
        if self.icon_file is not None:
            dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.icon_file))
        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.destroy()

    def handler_create_new(self, btn):
        system = SystemModel()
        system.id = ''
        system.user = shell_exec('whoami').strip()
        system.mount_point = '/home/%s/' % system.user
        system.mount_opts = ['follow_symlinks', 'workaround=rename']
        RecordRenderer(self, system, added=False).render()

    def handler_edit(self, btn, system_id):
        system = self._get_system_by_id(system_id)
        RecordRenderer(self, system, added=True).render()

    def handler_clone(self, btn, system_id):
        system = self._get_system_by_id(system_id)
        system.id = system.id + '-clone'
        RecordRenderer(self, system, added=False).render()

    def handler_delete(self, btn, system_id):
        system = self._get_system_by_id(system_id)
        text = 'Delete definition for `%s`?' % system_id
        dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL, Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE, text)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.NO)
        dialog.add_button(Gtk.STOCK_DELETE, Gtk.ResponseType.YES)
        dialog.set_title(text)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            controller = SystemControllerModel(system, self.environment)
            controller.unmount()
            system.delete(self.environment)
            self.refresh_list()

    def refresh_list(self):
        ids_mounted = self.environment.get_mounted_ids()

        for child in self.list_container.get_children():
            self.list_container.remove(child)

        ids_available = self.environment.get_available_ids()

        empty_list_message = 'No sftp systems defined yet.'

        if self.list_filter_text not in [None, '']:
            empty_list_message = 'No sftp systems match your search criteria.'
            ids_available = [id for id in ids_available if id.startswith(self.list_filter_text)]

        for system_id in ids_available:
            is_mounted = system_id in ids_mounted

            hbox = create_hbox()

            def on_switch_activated(switch, gparam, system_id):
                if switch.get_active():
                    self.handler_mount_by_id(system_id)
                else:
                    self.handler_unmount_by_id(system_id)

            switch = Gtk.Switch()
            switch.set_name('Mount')
            switch.set_tooltip_text('Mount or unmount this filesystem')
            switch.props.valign = Gtk.Align.CENTER
            switch.set_margin_start(10)
            switch.set_margin_end(10)
            switch.set_active(is_mounted)
            switch.connect("notify::active", on_switch_activated, system_id)
            hbox.pack_start(switch, False, True, 0)

            # Sftp system id
            label = Gtk.Label(label=system_id)
            label.set_alignment(0, 0)
            label.set_size_request(150, 35)
            hbox.pack_start(label, True, True, 0)

            btn_open = Gtk.Button()
            btn_open.set_label('Open')
            btn_open.set_image(Gtk.Image.new_from_icon_name('document-open', Gtk.IconSize.BUTTON))
            btn_open.set_always_show_image(True)
            btn_open.set_tooltip_text('Opens this filesystem')
            btn_open.set_sensitive(is_mounted)
            btn_open.set_size_request(120, 35)
            btn_open.connect("clicked", self.handler_open_by_id, system_id)

            hbox.pack_start(btn_open, False, True, 0)

            btn_hamburger = self._create_hamburger_menu_for_system(system_id)
            btn_hamburger.set_margin_end(10)

            hbox.pack_start(btn_hamburger, False, True, 0)

            row = Gtk.ListBoxRow()
            row.add(hbox)
            self.list_container.add(row)

        if len(ids_available) == 0:
            label = Gtk.Label(label=empty_list_message)
            label.set_justify(Gtk.Justification.CENTER)
            self.list_container.add(label)

        self.list_container.show_all()

    def _create_hamburger_menu_for_system(self, system_id):
        btn_edit = Gtk.ModelButton()
        btn_edit.set_label('Edit')
        btn_edit.set_image(Gtk.Image.new_from_icon_name('preferences-system', Gtk.IconSize.MENU))
        btn_edit.set_always_show_image(False)
        btn_edit.set_tooltip_text("Edit this filesystem's settings")
        btn_edit.set_alignment(0, 0.5) # Left-align
        btn_edit.connect("clicked", self.handler_edit, system_id)

        btn_clone = Gtk.ModelButton()
        btn_clone.set_label('Clone')
        btn_clone.set_image(Gtk.Image.new_from_icon_name('edit-copy', Gtk.IconSize.MENU))
        btn_clone.set_always_show_image(False)
        btn_clone.set_tooltip_text("Duplicate this filesystem's settings into a new filesystem")
        btn_clone.set_alignment(0, 0.5) # Left-align
        btn_clone.connect("clicked", self.handler_clone, system_id)

        btn_delete = Gtk.ModelButton()
        btn_delete.set_label('Delete')
        btn_delete.set_image(Gtk.Image.new_from_icon_name('edit-delete', Gtk.IconSize.BUTTON))
        btn_delete.set_always_show_image(True)
        btn_delete.set_tooltip_text("Deletes this filesystem definition")
        btn_delete.set_alignment(0, 0.5) # Left-align
        btn_delete.show()
        btn_delete.connect("clicked", self.handler_delete, system_id)

        popover_vbox = create_vbox()
        popover_vbox.pack_start(btn_edit, False, True, 0)
        popover_vbox.pack_start(btn_clone, False, True, 0)
        popover_vbox.pack_start(btn_delete, False, True, 0)
        popover_vbox.show_all()

        popover = Gtk.Popover()
        popover.add(popover_vbox)

        btn_hamburger = Gtk.MenuButton(popover=popover)
        btn_hamburger.set_label('')
        btn_hamburger.set_image(Gtk.Image.new_from_icon_name('open-menu-symbolic', Gtk.IconSize.BUTTON))
        btn_hamburger.set_always_show_image(False)
        btn_hamburger.set_tooltip_text("Show additional options")

        return btn_hamburger

    def show_list(self):
        self.list_container_wrapper.show()
        self.in_list_mode = True

    def hide_list(self):
        self.list_container_wrapper.hide()
        self.in_list_mode = False

    def _create_header_bar(self):
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)

        btn_add_new = Gtk.Button()
        btn_add_new.set_label('New')
        btn_add_new.set_image(Gtk.Image.new_from_icon_name('document-new', Gtk.IconSize.LARGE_TOOLBAR))
        btn_add_new.set_always_show_image(True)
        btn_add_new.set_tooltip_text('Add a new filesystem')
        btn_add_new.connect("clicked", self.handler_create_new)
        self.header_bar.pack_start(btn_add_new)

        btn_about = Gtk.Button()
        btn_about.set_image(Gtk.Image.new_from_icon_name('help-about', Gtk.IconSize.LARGE_TOOLBAR))
        btn_about.connect("clicked", self.handler_about)
        self.header_bar.pack_end(btn_about)

        self.btn_mount_search = Gtk.ToggleButton()
        self.btn_mount_search.set_label('Search')
        self.btn_mount_search.set_image(Gtk.Image.new_from_icon_name('search', Gtk.IconSize.LARGE_TOOLBAR))
        self.btn_mount_search.set_always_show_image(True)
        self.btn_mount_search.set_tooltip_text('Searches the list [Ctrl + F or Ctrl + K]')
        self.btn_mount_search.connect("toggled", self.handler_toggle_search)
        self.btn_mount_search.set_active(self.search_bar.get_search_mode())
        self.header_bar.pack_end(self.btn_mount_search)

        btn_unmount_all = Gtk.Button()
        btn_unmount_all.set_label('Unmount all')
        btn_unmount_all.set_image(Gtk.Image.new_from_icon_name('network-offline', Gtk.IconSize.LARGE_TOOLBAR))
        btn_unmount_all.set_always_show_image(True)
        btn_unmount_all.set_tooltip_text('Unmounts all filesystems')
        btn_unmount_all.connect("clicked", self.handler_unmount_all)
        self.header_bar.pack_end(btn_unmount_all)

        btn_mount_all = Gtk.Button()
        btn_mount_all.set_label('Mount all')
        btn_mount_all.set_image(Gtk.Image.new_from_icon_name('network-idle', Gtk.IconSize.LARGE_TOOLBAR))
        btn_mount_all.set_always_show_image(True)
        btn_mount_all.set_tooltip_text('Mounts all filesystems')
        btn_mount_all.connect("clicked", self.handler_mount_all)
        self.header_bar.pack_end(btn_mount_all)

        return self.header_bar

    def _create_list_container(self):
        # This would contain the sftp systems list
        self.list_container = Gtk.ListBox()
        self.list_container.set_selection_mode(Gtk.SelectionMode.NONE)
        self.refresh_list()
        return self.list_container

    def _create_record_container(self):
        # This would contain the form entries when adding/editing systems
        self.record_container = create_vbox()
        return self.record_container

    def _create_search_bar(self):
        def search_changed_handler(search_entry):
            self.list_filter_text = search_entry.get_text()
            self.refresh_list()

        search_entry = Gtk.SearchEntry()
        search_entry.set_placeholder_text('Search..')
        search_entry.set_size_request(400, -1)
        search_entry.connect("search-changed", search_changed_handler)
        search_entry.show()

        search_bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        search_bar_box.pack_start(search_entry, True, True, 0)
        search_bar_box.show()

        search_bar = Gtk.SearchBar()
        search_bar.add(search_bar_box)
        search_bar.connect_entry(search_entry)
        search_bar.show()

        return search_bar

    def _on_window_key_press(self, window, event, search_bar):
        if event.type == Gdk.EventType.KEY_PRESS and event.keyval == Gdk.KEY_Escape:
            search_bar.set_search_mode(False)
            self.btn_mount_search.set_active(self.search_bar.get_search_mode())
            return

        if event.type == Gdk.EventType.KEY_PRESS and \
            (
                (event.keyval == ord('f') and event.state & Gdk.ModifierType.CONTROL_MASK)
                or
                (event.keyval == ord('k') and event.state & Gdk.ModifierType.CONTROL_MASK)
            ):
            search_bar.set_search_mode(not search_bar.get_search_mode())
            self.btn_mount_search.set_active(self.search_bar.get_search_mode())
            return

    def __init__(self):
        self.environment = EnvironmentModel()

        self.list_filter_text = None

        self.search_bar = self._create_search_bar()

        self.window = Gtk.Window()
        self.window.set_title('SftpMan')
        self.window.set_default_size(-1, 600)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect('destroy', self.handler_destroy)

        self.icon_file = os.path.join(os.path.dirname(__file__), '..', 'sftpman-gtk.png')
        if not os.path.exists(self.icon_file):
            self.icon_file = '/usr/share/pixmaps/sftpman-gtk.png'
            if not os.path.exists(self.icon_file):
                self.icon_file = None
        if self.icon_file is not None:
            self.window.set_icon_from_file(self.icon_file)

        self.window.set_titlebar(self._create_header_bar())

        self.list_container_wrapper = Gtk.ScrolledWindow()
        self.list_container_wrapper.add_with_viewport(self._create_list_container())

        self.window.connect("key-press-event", self._on_window_key_press, self.search_bar)

        vbox_main = create_vbox()
        vbox_main.pack_start(self.search_bar, False, True, 0)
        vbox_main.pack_start(self.list_container_wrapper, True, True, 0)
        vbox_main.pack_start(self._create_record_container(), False, False, 0)

        self.vbox_main = vbox_main

        self.window.add(vbox_main)
        self.window.show_all()

        self.in_list_mode = True

        def list_periodic_refresher():
            while True:
                # Trying to update the GTK GUI from a thread causes
                # a segmentation fault - this is the proper way to do it
                if self.in_list_mode:
                    GLib.idle_add(self.refresh_list)
                sleep(15)

        refresher_thread = Thread(target=list_periodic_refresher)
        refresher_thread.daemon = True
        refresher_thread.start()

    def _perform_preflight_check(self):
        checks_pass, failures = self.environment.perform_preflight_check()
        if not checks_pass:
            for msg in failures:
                show_warning_message(self.window, msg)
            show_warning_message(self.window, 'Mounting will fail until all problems are fixed.')

    def main(self):
        self._perform_preflight_check()
        Gtk.main()


class RecordRenderer(object):
    """Deals with the record form (Adding/Editing sftp systems)."""

    def __init__(self, window_obj, system, added):
        self.window_obj = window_obj
        self.environment = self.window_obj.environment
        self.system = system
        self.system_id_before = system.id
        self.added = added

        self.window_obj.hide_list()
        for child in self.window_obj.header_bar.get_children():
            child.set_sensitive(False)

        self.rendered_fields = []

        self.action_bar = Gtk.ActionBar()

        btn_save = Gtk.Button()
        btn_save.set_label('Save')
        btn_save.set_image(Gtk.Image.new_from_icon_name('document-save', Gtk.IconSize.BUTTON))
        btn_save.set_always_show_image(True)
        btn_save.show()
        btn_save.connect("clicked", self.handler_save)

        btn_back = Gtk.Button()
        btn_back.set_label('Cancel')
        btn_back.set_image(Gtk.Image.new_from_icon_name('object-rotate-left', Gtk.IconSize.BUTTON))
        btn_back.set_always_show_image(True)
        btn_back.show()
        btn_back.connect("clicked", self.handler_cancel)

        self.action_bar.pack_start(btn_save)
        self.action_bar.pack_end(btn_back)

        self.window_obj.vbox_main.pack_end(self.action_bar, False, False, 0)
        self.action_bar.show()

        self.hbox_key_file = None
        self.combobox_auth_method = None

    def get_field_definitions(self):
        return (
            {'id': 'id', 'type': 'textbox', 'title': 'Identifier'},
            {'id': 'host', 'type': 'textbox', 'title': 'Host', 'disabled': False},
            {'id': 'port', 'type': 'textbox', 'title': 'Port', 'disabled': False},
            {'id': 'user', 'type': 'textbox', 'title': 'Username', 'disabled': False},
            {'id': 'auth_method', 'type': 'combobox_auth_method', 'title': 'Authentication method', 'disabled': False},
            {'id': 'ssh_key', 'type': 'key_filepath', 'title': 'SSH key', 'disabled': False},
            {'id': 'mount_point', 'type': 'textbox', 'title': 'Remote mount point', 'disabled': False},
            {'id': 'mount_opts', 'type': 'options', 'title': 'Options', 'disabled': False},
            {'id': 'cmd_before_mount', 'type': 'textbox', 'title': 'Run before mount', 'disabled': False},
        )

    def get_field_value(self, field_name):
        value = getattr(self.system, field_name, None)
        return value if value is not None else ''

    auth_methods = (
        (SystemModel.AUTH_METHOD_PUBLIC_KEY, 'Public key'),
        (SystemModel.AUTH_METHOD_AUTHENTICATION_AGENT, 'SSH agent'),
        (SystemModel.AUTH_METHOD_PASSWORD, 'Password'),
    )

    def render_combobox_auth_method(self, field_info):
        self.combobox_auth_method = Gtk.ComboBoxText()
        selected_index = 0
        selected_auth_method = self.system.auth_method
        for index, (key, title) in enumerate(self.auth_methods):
            if key == selected_auth_method:
                selected_index = index
            self.combobox_auth_method.insert_text(index, title)
        self.combobox_auth_method.set_active(selected_index)
        self.combobox_auth_method.connect('changed', self.on_auth_method_changed)
        return self.combobox_auth_method

    def on_auth_method_changed(self, combo):
        auth_method = self.get_value_combobox_auth_method(combo)
        if auth_method == SystemModel.AUTH_METHOD_PUBLIC_KEY:
            self.hbox_key_file.set_sensitive(True)
        else:
            self.hbox_key_file.set_sensitive(False)

    def get_value_combobox_auth_method(self, widget):
        selected_index = widget.get_active()
        try:
            auth_method, _ = self.auth_methods[selected_index]
            return auth_method
        except IndexError:
            return None

    def render_textbox(self, field_info):
        textbox = Gtk.Entry()
        textbox.set_text(str(self.get_field_value(field_info['id'])))
        if field_info.get('disabled', False):
            textbox.set_sensitive(False)
        return textbox

    def get_value_textbox(self, widget):
        return widget.get_text()

    def render_key_filepath(self, field_info):
        path_now = self.get_field_value(field_info['id'])

        textbox = Gtk.Entry()
        textbox.set_text(path_now)

        def filechooser_start(btn):
            buttons = ('Cancel', Gtk.ResponseType.CANCEL, 'Open', Gtk.ResponseType.OK)
            filechooser = Gtk.FileChooserDialog('Select your private ssh key file:', self.window_obj.window, Gtk.FileChooserAction.OPEN, buttons)
            if os.path.exists(path_now):
                start_path = os.path.dirname(path_now)
            else:
                home_path = os.path.expanduser('~')
                ssh_path = '%s/.ssh/' % home_path
                start_path = ssh_path if os.path.exists(ssh_path) else home_path
            filechooser.set_current_folder(start_path)

            if filechooser.run() == Gtk.ResponseType.OK:
                textbox.set_text(filechooser.get_filename())

            filechooser.destroy()

        btn_browse = Gtk.Button()
        btn_browse.set_image(Gtk.Image.new_from_icon_name('document-open', Gtk.IconSize.BUTTON))
        btn_browse.show()
        btn_browse.connect("clicked", filechooser_start)

        self.hbox_key_file = create_hbox()
        self.hbox_key_file.pack_start(textbox, True, True, 0)
        self.hbox_key_file.pack_start(btn_browse, False, False, 0)

        # Allow the changed handler for the auth method combobox to
        # enable/disable this SSH key chooser, depending on the auth method
        self.on_auth_method_changed(self.combobox_auth_method)

        return self.hbox_key_file

    def get_value_key_filepath(self, widget):
        textbox = widget.get_children()[0]
        return textbox.get_text()

    def render_options(self, field_info):
        options = self.get_field_value(field_info['id'])
        textbox = Gtk.Entry()
        textbox.set_text(', '.join(options))
        return textbox

    def get_value_options(self, widget):
        widget_text = widget.get_text().strip()
        if widget_text == '':
            return []
        return [option.strip() for option in widget_text.split(',')]

    def handler_save(self, btn):
        controller = None
        is_mounted_before_save = False
        if self.added:
            controller = SystemControllerModel(self.system, self.environment)
            is_mounted_before_save = controller.mounted

        for field_info in self.rendered_fields:
            widget = field_info['widget']

            get_value_callback = getattr(self, 'get_value_%s' % field_info['type'], None)
            if get_value_callback is None:
                raise SftpException('Cannot get value for field type: %s' % field_info['type'])
            value = get_value_callback(widget)
            setattr(self.system, field_info['id'], value)

        is_valid, errors = self.system.validate()
        if not is_valid:
            for field_id, msg in errors:
                show_warning_message(self.window_obj.window, msg)
            return

        # Validation checks above only deal with the model's data, not with the system as a whole.
        # We'd like to ensure that the id is NOT a duplicate when:
        # - adding a brand new definition
        # - changing the id of an existing definition
        check_for_id_uniqueness = False
        if self.added:
            if self.system.id != self.system_id_before:
                check_for_id_uniqueness = True
        else:
            check_for_id_uniqueness = True

        if check_for_id_uniqueness:
            if self._is_system_id_in_use(self.system.id):
                msg = 'The identifier (%s) is already in use by another definition!' % self.system.id
                show_warning_message(self.window_obj.window, msg)
                return

        if is_mounted_before_save and controller is not None:
            controller.unmount()

        self.system.save(self.environment)

        if self.added and self.system.id != self.system_id_before:
            # The ID got changed and we saved a new system definition.
            # Time to purge the old one now.
            old_system = SystemModel.create_by_id(self.system_id_before, self.environment)
            old_system.delete(self.environment)

        if is_mounted_before_save:
            # We must create a new controller, because the system definition
            # (including the ID) may have changed.
            controller = SystemControllerModel(self.system, self.environment)
            controller.mount()

        self.close()

    def handler_cancel(self, btn):
        self.close()

    def close(self):
        # Get rid of all the fields we rendered in the record container,
        # but preserve the container for later use
        for child in self.window_obj.record_container.get_children():
            self.window_obj.record_container.remove(child)
        self.window_obj.refresh_list()
        self.window_obj.show_list()

        for child in self.window_obj.header_bar.get_children():
            child.set_sensitive(True)
        self.window_obj.vbox_main.remove(self.action_bar)

    def _is_system_id_in_use(self, system_id):
        try:
            SystemModel.create_by_id(system_id, self.environment)
            return True
        except SftpConfigException:
            return False

    def render(self):
        for child in self.window_obj.record_container.get_children():
            self.window_obj.record_container.remove(child)

        self.rendered_fields = []

        grid = create_grid()

        for row_number, field_info in enumerate(self.get_field_definitions()):
            label = Gtk.Label(label=field_info['title'])
            # Align left (horizontally) and middle (vertically)
            label.set_alignment(0, 0.5)
            label.set_margin_start(10)

            render_callback = getattr(self, 'render_%s' % field_info['type'], None)
            if render_callback is None:
                raise SftpException('Missing renderer for field type %s' % field_info['type'])
            widget = render_callback(field_info)
            widget.set_hexpand(True)

            grid.attach(label, 0, row_number, 1, 1)
            grid.attach(widget, 1, row_number, 1, 1)

            field_info['widget'] = widget
            self.rendered_fields.append(field_info)

        self.window_obj.record_container.pack_start(grid, True, True, 0)
        self.window_obj.record_container.show_all()

        if not self.added:
            # Give focus to the first field in the form
            self.rendered_fields[0]['widget'].grab_focus()


def start():
    obj = SftpManGtk()
    obj.main()
