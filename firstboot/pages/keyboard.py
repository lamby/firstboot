import fnmatch
import collections

from gi.repository import Gtk, Gdk

from ..utils import find_data, load_data

from .base import Page, LABEL_PADDING

LABEL = """
<b>Please select your keyboard layout</b>
"""


class Keyboard(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.iters = {}
        self.model = Gtk.TreeStore(str, str, str)
        self.selected = None

        self.locales = collections.OrderedDict()
        self.layouts = collections.OrderedDict()

        for x in load_data(find_data('kbdnames')):
            lang, type_, layout_code, data = x.split('*', 3)

            if lang != 'C':
                continue

            if type_ == 'layout':
                self.layouts[layout_code] = {
                    'code': layout_code,
                    'title': data,
                    'variants': collections.OrderedDict(),
                }
            elif type_ == 'variant':
                variant_code, title = data.split('*', 1)

                if not variant_code:
                    continue

                parent = self.layouts[layout_code]
                title = title.replace("{title} - ".format(**parent), '')

                parent['variants'][variant_code] = {
                    'code': variant_code,
                    'title': title,
                }

        for x in load_data(find_data('keyboard-configuration')):
            wildcard, _, data = x.partition('\t')
            layout_codes, _, variant_code = data.partition('\t')
            layout_code, _, _ = layout_codes.partition(',')
            variant_code = variant_code.replace(',', '')

            try:
                self.layouts[layout_code][variant_code]
                self.locales[wildcard] = (layout_code, variant_code)
            except KeyError:
                pass

        # Populate model
        for layout in self.layouts.values():
            it = self.model.append(None, [layout['code'], '', layout['title']])

            self.iters[(layout['code'], '')] = it

            for variant in layout['variants'].values():
                key = layout['code'], variant['code']

                self.iters[key] = self.model.append(
                    it, [layout['code'], variant['code'], variant['title']],
                )

        self.treeview = Gtk.TreeView(self.model, headers_visible=False)
        self.treeview.connect('row-activated', self.on_row_activated)
        self.treeview.connect('key-press-event', self.on_key_press_event)

        selection = self.treeview.get_selection()
        selection.connect('changed', self.on_changed)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("", renderer, text=2)
        self.treeview.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.treeview)

        label = self.create_label(LABEL)

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(scroll, True, True, 0)
        self.pack_start(vbox, True, True, 0)

    def get_apply_data(self):
        return {
            'keyboard_layout': self.selected[0] if self.selected else None,
            'keyboard_variant': self.selected[1] if self.selected else None,
        }

    def on_switch(self):
        self.treeview.grab_focus()

        # Try and determine a default
        if not self.selected:
            data = self.assistant.get_all_apply_data()

            # FIXME: use the field in languagelist
            locale = '{language}_{country}'.format(**data)

            # Set a fallback
            self.selected = ('us', '')

            for k, v in self.locales.items():
                if not fnmatch.fnmatch(locale, k):
                    continue

                self.selected = v
                break

        it = self.iters[self.selected]
        path = self.model.get_path(it)
        self.treeview.get_selection().select_iter(it)
        self.treeview.scroll_to_cell(path, None, True, 0.5, 0)

    def on_changed(self, selection):
        model, treeiter = selection.get_selected()
        self.selected = None
        if treeiter:
            self.selected = model[treeiter][0], model[treeiter][1]
        self.assistant.set_page_complete(self, bool(self.selected))

    def on_row_activated(self, treeview, path, column):
        it = self.model.get_iter(path)
        value = self.model.get_value(it, 0), self.model.get_value(it, 1)

        self.selected = value
        self.assistant.notebook.next_page()

    def on_key_press_event(self, widget, event):
        if event.keyval != Gdk.KEY_Return:
            return

        if self.selected:
            self.assistant.notebook.next_page()
