import re

from gi.repository import Gtk

LABEL_PADDING = 25


class Page(Gtk.Box):
    def __init__(self, name, assistant):
        self.name = name
        self.assistant = assistant

        self.complete = False

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

    def get_apply_data(self):
        return {}

    def is_valid(self):
        try:
            self.validate(self.get_apply_data())
        except ValidationError:
            return False

        return True

    def validate(self, data):
        pass

    def on_switch(self):
        pass

    def render_validation_errors(self, label):
        """
        Returns ``True`` if there are no validation errors.
        """

        try:
            self.validate(self.get_apply_data())
        except ValidationError as exc:
            label.set_markup(str(exc))
            return False

        label.set_markup('')

        return True

    def create_label(self, markup='', *args, **kwargs):
        markup = markup.strip()

        # Normalise to maximum of 2 newlines
        markup = re.sub(r'\n{2,}', '\n\n', markup)

        # Replace single newlines with a space
        markup = re.sub(r'(?<!\n)\n(?!\n)', ' ', markup)

        label = Gtk.Label()
        label.set_markup(markup)
        label.set_justify(Gtk.Justification.LEFT)
        label.set_line_wrap(True)

        return label


class ValidationError(Exception):
    pass
