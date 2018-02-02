import re
import json
import operator
import collections

from gi.repository import Gtk, Gdk

from ..utils import find_data, load_data

from .base import Page, LABEL_PADDING

LABEL = """
<b>Select your location.</b>

The selected location will be used to set your time zone and also for example
to help select the system locale. Normally this should be the country where you
live.
"""

cmp_title = operator.itemgetter('title')
re_supported = re.compile(
    r'^(?P<language_code>[^_]+)_(?P<country_code>[^@. ]+)'
)


class Country(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.model = Gtk.TreeStore(str, str)
        self.iters = {}
        self.selected = None

        self.regions = collections.OrderedDict()
        self.defaults = {'en': 'US'} # FIXME we can do this properly from languagelist
        self.countries = collections.OrderedDict()
        self.shortlist = {}

        # Parse data
        with open('/usr/share/iso-codes/json/iso_3166-1.json') as f:
            title_lookup = {
                x['alpha_2']: x['name'] for x in json.load(f)['3166-1']
            }

        for x in load_data(find_data('regionmap')):
            country_code, region_title = x.split('\t', 1)

            if region_title == "Other":
                continue

            self.regions.setdefault(region_title, {
                'title': region_title,
                'countries': collections.OrderedDict(),
                'country_codes': set()
            })['country_codes'].add(country_code)

        for x in load_data('/usr/share/i18n/SUPPORTED'):
            m = re_supported.match(x)

            if m is None:
                continue

            country_code = m.group('country_code')
            language_code = m.group('language_code')

            self.countries[country_code] = {
                'code': country_code,
                'title': title_lookup[country_code],
            }

            # Don't add Denmark to shortlist for English (#276067)
            if (language_code, country_code) == ('en', 'DK'):
                continue

            self.shortlist.setdefault(language_code, {})[country_code] = {
                'title': title_lookup[country_code],
                'country_code': country_code,
                'language_code': language_code,
            }

        self.treeview = Gtk.TreeView(self.model, headers_visible=False)
        self.treeview.connect('row-activated', self.on_row_activated)
        self.treeview.connect('key-press-event', self.on_key_press_event)

        selection = self.treeview.get_selection()
        self.change_handler = selection.connect('changed', self.on_changed)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("", renderer, text=1)
        self.treeview.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.add(self.treeview)

        vbox = Gtk.VBox()
        vbox.pack_start(label, False, False, LABEL_PADDING)
        vbox.pack_start(scroll, True, True, 0)
        self.pack_start(vbox, True, True, 0)

    def get_apply_data(self):
        return {
            'country': self.selected,
        }

    def on_switch(self):
        selection = self.treeview.get_selection()
        selection.handler_block(self.change_handler)

        # Populate model
        self.model.clear()
        self.iters = {}

        # eg. zh_CN -> zh
        default_language, _, _ = self.assistant \
            .get_all_apply_data()['language'].partition('_')

        try:
            shortlist = self.shortlist[default_language]
        except KeyError:
            shortlist = self.shortlist['en']

        for country in sorted(shortlist.values(), key=cmp_title):
            self.iters[country['country_code']] = self.model.append(
                None, [country['country_code'], country['title']],
            )

        other_it = self.model.append(None, [None, "Other"])

        # Loop over all regions...
        for region in sorted(self.regions.values(), key=cmp_title):
            region_it = self.model.append(other_it, [None, region['title']])

            # ... then all countries, skipping ones that don't match the region
            for country in sorted(self.countries.values(), key=cmp_title):
                if country['code'] not in region['country_codes']:
                    continue

                country_it = self.model.append(
                    region_it, [country['code'], country['title']],
                )

                # Don't overwrite iter in shortlist
                self.iters.setdefault(country['code'], country_it)

        # Grab focus prior to unblocking change handler
        self.treeview.grab_focus()

        selection.handler_unblock(self.change_handler)

        # Set a default for this country if we have one
        if not self.selected:
            try:
                self.selected = self.defaults[default_language]
            except KeyError:
                if len(shortlist) == 1:
                    self.selected = list(shortlist.values())[0]['country_code']

        self.treeview.get_selection().unselect_all()
        self.assistant.set_page_complete(self, bool(self.selected))

        if not self.selected:
            return

        it = self.iters[self.selected]
        path = self.model.get_path(it)
        self.treeview.expand_to_path(path)
        self.treeview.scroll_to_cell(path, None, True, 0.5, 0)
        self.treeview.get_selection().select_iter(it)

    def on_changed(self, selection):
        model, treeiter = selection.get_selected()
        if treeiter:
            self.selected = model[treeiter][0]
        self.assistant.set_page_complete(self, bool(self.selected))

        # Reset stuff if we pressed 'Back'
        timezone_page = \
            self.assistant.pages['firstboot.pages.timezone.Timezone']
        timezone_page.selected = None

        keyboard_page = \
            self.assistant.pages['firstboot.pages.keyboard.Keyboard']
        keyboard_page.selected = None

    def on_row_activated(self, treeview, path, column):
        self.selected = self.model.get_value(self.model.get_iter(path), 0)

        if self.selected:
            self.assistant.notebook.next_page()
        else:
            if treeview.row_expanded(path):
                treeview.collapse_row(path)
            else:
                treeview.expand_to_path(path)

    def on_key_press_event(self, widget, event):
        if event.keyval != Gdk.KEY_Return:
            return

        if self.selected:
            self.assistant.notebook.next_page()
