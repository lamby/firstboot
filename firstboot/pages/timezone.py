import re
import json
import operator
import collections

from gi.repository import Gtk, Gdk

from ..utils import find_data, load_data

from .base import Page, LABEL_PADDING

LABEL = """
<b>Select your timezone.</b>
"""

cmp_title = operator.itemgetter('title')


class Timezone(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)

        self.model = Gtk.TreeStore(str, str)
        self.iters = {}
        self.selected = None

        self.areas = {}
        self.countries = {}

        def timezone_to_title(val):
            return val.split('/', 1)[1].replace('_', ' ')

        # Parse data
        for x in load_data('/usr/share/zoneinfo/zone.tab'):
            xs = x.split('\t')

            country_code, timezone_code = xs[0], xs[2]

            area_title, _, with_subarea = timezone_code.partition('/')
            subarea_title, _, timezone_title = with_subarea.partition('/')

            area = self.areas.setdefault(area_title, {
                'title': area_title,
                'subareas': {}
            })

            subarea = area['subareas'].setdefault(subarea_title, {
                'title': subarea_title.replace('_', ' '),
                'timezones': {},
            })

            subarea['timezones'].setdefault(timezone_code, {
                'code': timezone_code,
                'title': timezone_title.replace('_', ' ') or subarea['title'],
            })

            self.countries.setdefault(country_code, []).append(timezone_code)

        for x in load_data(find_data('tzmap.override')):
            country_code, timezone = x.split(' ', 1)
            self.countries[country_code] = [timezone]

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
            'timezone': self.selected,
        }

    def on_switch(self):
        selection = self.treeview.get_selection()
        selection.handler_block(self.change_handler)

        # Populate model
        self.model.clear()
        self.iters = {}

        country_code = self.assistant.get_all_apply_data()['country']
        shortlist = self.countries[country_code]

        other_it = self.model.append(None, [None, "Other"])

        # Loop over all areas
        for area in sorted(self.areas.values(), key=cmp_title):
            area_it = self.model.append(other_it, [None, area['title']])

            # ... then over each subarea
            for subarea in sorted(area['subareas'].values(), key=cmp_title):
                # Only show subareas if we have them
                subarea_it = area_it
                if len(subarea['timezones']) > 1:
                    subarea_it = self.model.append(
                        area_it, [None, subarea['title']],
                    )

                # ... then over each timezone
                subareas = subarea['timezones'].values()
                for timezone in sorted(subareas, key=cmp_title):
                    code = timezone['code']

                    # Add to top-level shortlist
                    if code in shortlist:
                        self.iters[code] = self.model.insert_before(
                            None, other_it, [code, timezone['title']]
                        )

                    it = self.model.append(
                        subarea_it, [code, timezone['title']]
                    )

                    # Don't override any previous iter
                    self.iters.setdefault(code, it)

        # Grab focus prior to unblocking change handler
        self.treeview.grab_focus()

        selection.handler_unblock(self.change_handler)

        # Set a default for this country if we have one
        if not self.selected and shortlist:
            self.selected = shortlist[0]

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
