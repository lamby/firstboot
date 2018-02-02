from .base import Page, LABEL_PADDING

LABEL = """
<b>We are now ready to setup your system.</b>

Press the 'Apply' button to explicitly set the changes, or 'Go Back' to correct
any mistakes.
"""


class Done(Page):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        label = self.create_label(LABEL)
        self.pack_start(label, True, True, LABEL_PADDING)

        self.assistant.set_page_complete(self, True)

    def on_switch(self):
        self.assistant.btn_apply.grab_focus()
