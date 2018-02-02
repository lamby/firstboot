#!/usr/bin/env python3

import logging

from gi.repository import Gtk, GdkPixbuf

from .utils import find_data, import_from_string
from .apply_data import ApplyData

PAGES = (
    'firstboot.pages.welcome.Welcome',
    'firstboot.pages.language.Language',
    'firstboot.pages.country.Country',
    'firstboot.pages.timezone.Timezone',
    'firstboot.pages.keyboard.Keyboard',
    'firstboot.pages.full_name.FullName',
    'firstboot.pages.username.Username',
    'firstboot.pages.password.Password',
    'firstboot.pages.hostname.Hostname',
    'firstboot.pages.done.Done',
)

logger = logging.getLogger(__name__)


class Assistant(Gtk.Window):
    def __init__(self, development):
        Gtk.Window.__init__(self)

        self.complete = False
        self.development = development

        self.apply_data = ApplyData(no_act=self.development)

        self.connect('delete-event', self.on_delete_event)
        self.set_default_size(800, 650)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Add image
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            find_data('header.svg'),
            self.get_size()[0],
            -1,
            True,
        )
        image = Gtk.Image()
        image.set_from_pixbuf(pixbuf)

        self.notebook = Gtk.Notebook(show_tabs=False)

        # Action buttons
        self.btn_prev = Gtk.Button(
            "_Previous", use_underline=True, no_show_all=True,
        )
        self.btn_next = Gtk.Button(
            "_Next", use_underline=True, no_show_all=True,
        )
        self.btn_apply = Gtk.Button(
            "_Apply", use_underline=True, no_show_all=True,
        )

        self.btn_apply.connect('clicked', self.on_btn_apply_clicked)

        action_box = Gtk.HBox(spacing=6, border_width=6)
        action_box.pack_end(self.btn_apply, False, False, 0)
        for x in (self.btn_next, self.btn_prev):
            action_box.pack_end(x, False, False, 0)
            x.connect('clicked', self.on_btn_prev_next_clicked)

        vbox = Gtk.VBox()
        vbox.pack_start(image, False, False, 0)
        vbox.pack_start(self.notebook, True, True, 0)
        vbox.pack_start(action_box, False, False, 0)
        self.add(vbox)

        self.pages = {}
        for x in PAGES:
            page = import_from_string(x)(x, self)
            page.set_border_width(20)

            self.pages[x] = page
            self.notebook.append_page(page)

        # Bind late
        self.notebook.connect('switch-page', self.on_switch_page)

    def set_page_complete(self, page, complete):
        page.complete = complete
        self.btn_next.set_sensitive(complete)

    def on_switch_page(self, notebook, page, page_num):
        logger.info("Switching page to %s", page.name)
        logger.debug("get_all_apply_data() -> %s", self.get_all_apply_data())

        last_page = page_num + 1 == self.notebook.get_n_pages()

        self.btn_next.set_visible(not last_page)
        self.btn_next.set_sensitive(page.complete)
        self.btn_prev.set_visible(page_num > 0)
        self.btn_apply.set_visible(last_page)

        self.unset_focus_chain()

        page.on_switch()

    def get_all_apply_data(self):
        data = {}

        for x in self.pages.values():
            data.update(x.get_apply_data())

        return data

    def on_btn_prev_next_clicked(self, btn, *args):
        idx = self.notebook.get_current_page()
        delta = 1 if btn == self.btn_next else -1
        self.notebook.set_current_page(idx + delta)

    def on_btn_apply_clicked(self, *args):
        self.btn_prev.set_sensitive(False)
        self.btn_apply.set_sensitive(False)
        self.btn_apply.set_label("Please wait...")

        # Allow ourselves to quit
        self.complete = True

        self.apply_data.apply(self.get_all_apply_data())

    def on_delete_event(self, *args):
        if not self.development and not self.complete:
            return True

        Gtk.main_quit()
