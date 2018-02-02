import re
import subprocess

from gi.repository import Gtk, Gdk

from .base import Page, ValidationError, LABEL_PADDING

LABEL = """
<b>Please choose a hostname.</b>
"""


class Hostname(Page):
    re_valid = re.compile(r'^[a-z][-a-z0-9_]*$')

    min_length = 2
    max_length = 32

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_laptop = bool(subprocess.call('laptop-detect') == 0)

        label = self.create_label(LABEL)

        self.entry = Gtk.Entry()
        self.entry.set_max_length(self.max_length)
        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('key-press-event', self.on_key_press_event)

        self.errors = self.create_label()

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(self.entry, False, False, 0)
        vbox.pack_start(self.errors, False, False, LABEL_PADDING)

        self.pack_start(vbox, True, True, 0)

    def get_apply_data(self):
        return {
            'hostname': self.entry.get_text(),
        }

    def validate(self, data):
        val = data['hostname']

        if not val:
            raise ValidationError("Hostname cannot be blank.")

        if len(val) > self.max_length:
            raise ValidationError("Hostname is too long.")

        if val in {'localhost'}:
            raise ValidationError("This hostname is reserved.")

        if self.re_valid.match(val) is None:
            raise ValidationError("Hostname contains invalid characters.")

    def on_entry_changed(self, entry):
        is_valid = self.render_validation_errors(self.errors)

        self.assistant.set_page_complete(self, is_valid)

    def on_switch(self):
        if self.get_apply_data()['hostname']:
            return

        default = self.assistant.get_all_apply_data().get('username', '')

        # Add suffix
        default = '{}-{}'.format(
            default,
            'laptop' if self.is_laptop else 'pc',
        )

        # Only set a valid hostname
        try:
            self.validate({'hostname': default})
            self.entry.set_text(default)
        except ValidationError:
            pass

    def on_key_press_event(self, widget, event):
        # Ignore spaces
        if event.keyval == Gdk.KEY_space:
            return True

        if event.keyval == Gdk.KEY_Return and self.is_valid():
            self.assistant.notebook.next_page()
            return True

        return False
