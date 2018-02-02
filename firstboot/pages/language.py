import collections

from gi.repository import Gtk, Gdk

from ..utils import find_data, load_data

from .base import Page, LABEL_PADDING

LABEL = """
<b>Please choose your prefered language.</b>

This will be used for the default language on the installed system.
"""


class Language(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.model = Gtk.ListStore(str, str, str)
        self.selected = 'en'
        self.languages = collections.OrderedDict()

        for line in load_data(find_data('languagelist')):
            parsed = dict(zip((
                'langcode',
                'language_en',
                'language_orig',
                'supported_environments',
                'countrycode',
                'fallbacklocale',
                'langlist',
                'console-setup',
            ), line.split(';')))

            self.languages[parsed['langcode']] = parsed

        for x in self.languages.values():
            # Don't allow the "C" locale to be selected.
            if x['langcode'] == 'C':
                continue

            x['iter'] = self.model.append((
                x['langcode'],
                x['language_en'],
                x['language_orig']
                if x['language_orig'] != x['language_en'] else '',
            ))

        self.treeview = Gtk.TreeView(self.model, headers_visible=False)
        self.treeview.connect('row-activated', self.on_row_activated)
        self.treeview.connect('key-press-event', self.on_key_press_event)

        for idx in (1, 2):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('', renderer, text=idx)
            self.treeview.append_column(column)

        selection = self.treeview.get_selection()
        selection.connect('changed', self.on_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.treeview)

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(scroll, True, True, 0)
        self.pack_start(vbox, True, True, 0)

    def get_apply_data(self):
        return {
            'language': self.selected,
        }

    def on_switch(self):
        it = self.languages[self.selected]['iter']
        path = self.model.get_path(it)

        self.treeview.grab_focus()
        self.treeview.get_selection().select_iter(it)
        self.treeview.scroll_to_cell(path, None, True, 0.5, 0)

    def on_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter:
            self.selected = model[treeiter][0]

            # Reset region if we pressed 'Back'
            country_page = \
                self.assistant.pages['firstboot.pages.country.Country']
            country_page.selected = None

        self.assistant.set_page_complete(self, bool(self.selected))

    def on_row_activated(self, treeview, path, column):
        self.assistant.notebook.next_page()

    def on_key_press_event(self, widget, event):
        if event.keyval != Gdk.KEY_Return:
            return

        if self.selected:
            self.assistant.notebook.next_page()
