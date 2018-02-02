from .base import Page, LABEL_PADDING

LABEL = """
<b>Welcome to Debian GNU/Linux!</b>

There are a few steps to take before your system is ready to use. The following
screens will guide you through some basic configuration. Please click the
"Next" button in the lower right corner to continue.
"""


class Welcome(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)
        self.pack_start(label, True, True, LABEL_PADDING)

        self.assistant.set_page_complete(self, True)

    def on_switch(self):
        self.assistant.btn_next.grab_focus()
