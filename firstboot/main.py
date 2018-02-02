import os
import sys
import logging

from gi.repository import Gtk

from .assistant import Assistant
from .utils import setup_logging

log = logging.getLogger(__name__)


def main():
    development = os.environ.get('FIRSTBOOT_DEVELOPMENT_MODE') == '1'
    setup_logging(development)

    log.info("Starting firstboot (development mode: %s)", development)
    assistant = Assistant(development)

    log.debug("Showing GUI")
    assistant.show_all()

    try:
        Gtk.main()
    except KeyboardInterrupt:
        log.warning("Caught keyboard interrupt; exiting")
        sys.exit(2)

    log.info("Exiting")
    sys.exit(0)
