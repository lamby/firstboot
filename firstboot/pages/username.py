import re
import pwd

from gi.repository import Gtk, Gdk

from ..utils import load_data

from .base import Page, ValidationError, LABEL_PADDING

LABEL = """
<b>Select a username for the new account.</b>

Your first name is a reasonable choice. The username should start with a
lower-case letter, which can be followed by any combination of numbers and more
lower-case letters.
"""


class Username(Page):
    re_valid = re.compile(r'^[a-z][-a-z0-9_]*$')
    re_starts_with_lowercase = re.compile(r'^[a-z]')

    max_length = 32

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.entry = Gtk.Entry()
        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('key-press-event', self.on_key_press_event)
        self.entry.set_max_length(self.max_length)

        self.errors = self.create_label()

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(self.entry, False, False, 0)
        vbox.pack_start(self.errors, False, False, LABEL_PADDING)
        self.pack_start(vbox, True, True, 0)

        self.exists = {x[0] for x in pwd.getpwall()}
        self.reserved = {load_data('/usr/lib/user-setup/reserved-usernames')}

    def get_apply_data(self):
        return {
            'username': self.entry.get_text(),
        }

    def validate(self, data):
        val = data['username']

        if not val:
            raise ValidationError("Username cannot be blank.")

        if len(val) > self.max_length:
            raise ValidationError("Username is too long.")

        if self.re_starts_with_lowercase.match(val) is None:
            raise ValidationError(
                "Username must start with a lower-case letter.",
            )

        if val in self.exists:
            raise ValidationError("This username is already in use.")

        if val in self.reserved:
            raise ValidationError("This username is reserved.")

        # Do a final "sweep" last; we've emitted some nicer messages earlier
        if self.re_valid.match(val) is None:
            raise ValidationError("Username contains invalid characters.")

    def on_switch(self):
        # Are we returning to this page?
        if self.get_apply_data()['username']:
            return

        default = self.assistant.get_all_apply_data().get('full_name', '')

        # Only use the first word
        default = default.split(' ', 1)[0]

        # Set to lower-case
        default = default.lower()

        # Strip non-valid characters
        default = re.sub(r'[^-a-z0-9_]', '', default)

        # Only set a valid username
        try:
            self.validate({'username': default})
            self.entry.set_text(default)
        except ValidationError:
            pass

    def on_entry_changed(self, entry):
        is_valid = self.render_validation_errors(self.errors)

        self.assistant.set_page_complete(self, is_valid)

    def on_key_press_event(self, widget, event):
        # Ignore spaces
        if event.keyval == Gdk.KEY_space:
            return True

        if event.keyval == Gdk.KEY_Return and self.is_valid():
            self.assistant.notebook.next_page()
            return True

        return False
