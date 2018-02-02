from gi.repository import Gtk, Gdk

from .base import Page, ValidationError, LABEL_PADDING

LABEL = """
<b>Please enter your full name.</b>

This will be used by any program which displays or uses the user's real name.
"""


class FullName(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.entry = Gtk.Entry()
        self.entry.connect('changed', self.on_entry_changed)
        self.entry.connect('key-press-event', self.on_key_press_event)

        self.errors = self.create_label()

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(self.entry, False, False, 0)
        vbox.pack_start(self.errors, False, False, LABEL_PADDING)

        self.pack_start(vbox, False, False, 0)

    def get_apply_data(self):
        return {
            'full_name': self.entry.get_text().strip(),
        }

    def validate(self, data):
        if not data['full_name']:
            raise ValidationError("Name cannot be blank.")

    def on_switch(self):
        if not self.get_apply_data()['full_name']:
            self.entry.grab_focus()

    def on_entry_changed(self, entry):
        is_valid = self.render_validation_errors(self.errors)

        self.assistant.set_page_complete(self, is_valid)

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Return and self.is_valid():
            self.assistant.notebook.next_page()
            return True

        return False
