from gi.repository import Gtk, Gdk

from .base import Page, ValidationError, LABEL_PADDING

LABEL = """
<b>Choose a password for the new user.</b>

A good password will contain a mixture of letters, numbers and punctuation and
should be changed at regular intervals.
"""


class Password(Page):
    max_length = 40
    min_length = 6

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.entry = Gtk.Entry()
        self.entry_confirm = Gtk.Entry()

        for x in (self.entry_confirm, self.entry):
            x.connect('changed', self.on_any_entry_changed)
            x.connect('key-press-event', self.on_key_press_event)
            x.set_visibility(False)
            x.set_max_length(self.max_length)

        self.errors = self.create_label()

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(self.entry, False, False, 0)
        vbox.pack_start(self.entry_confirm, False, False, 0)
        vbox.pack_start(self.errors, False, False, LABEL_PADDING)

        self.pack_start(vbox, True, True, 0)

    def get_apply_data(self):
        return {
            'password': self.entry.get_text(),
            'password_confirm': self.entry_confirm.get_text(),
        }

    def validate(self, data):
        if not data['password']:
            if data['password_confirm']:
                raise ValidationError("Please enter a password.")
            raise ValidationError("Password cannot be blank.")

        if len(data['password']) < self.min_length:
            raise ValidationError(
                "Password is too short. Please choose a value at least {} "
                "characters in length".format(self.min_length),
            )

        if len(data['password']) > self.max_length:
            raise ValidationError("Password is too long.")

        if data['password'] != data['password_confirm']:
            raise ValidationError("Passwords do not match.")

    def on_any_entry_changed(self, entry):
        if entry == self.entry:
            is_valid = self.is_valid()
        else:
            is_valid = self.render_validation_errors(self.errors)

        self.assistant.set_page_complete(self, is_valid)

    def on_key_press_event(self, widget, event):
        if event.keyval != Gdk.KEY_Return:
            return

        if widget == self.entry and self.entry.get_text():
            self.entry_confirm.grab_focus()
        else:
            if self.is_valid():
                self.assistant.notebook.next_page()

        return False
