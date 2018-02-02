import os
import re
import shlex
import debconf
import logging
import importlib
import contextlib

from systemd.journal import JournalHandler


DATA_DIRS = (
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data'),
    '/usr/share/firstboot/data',
)

HOOK_DIRS = (
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hooks'),
    '/usr/share/firstboot/hooks',
)

logger = logging.getLogger(__name__)


def setup_logging(development):
    handlers = [JournalHandler()]

    if development:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname).1s: %(message)s',
        handlers=handlers,
    )


def find_data(filename):
    for prefix in DATA_DIRS:
        fullpath = os.path.join(prefix, filename)
        if not os.path.exists(fullpath):
            continue

        logger.debug("Resolving %s for %s", fullpath, filename)

        return fullpath

    raise FileNotFoundError("Could not find {}".format(filename))


def find_hooks(name):
    for prefix in HOOK_DIRS:
        fullpath = os.path.join(prefix, name)
        if not os.path.isdir(fullpath):
            continue

        logger.debug("Resolving %s for %s", fullpath, name)

        return fullpath

    raise FileNotFoundError("Could not find hook directory {}".format(name))


def load_data(filename):
    logger.debug("Parsing %s", filename)

    with open(filename, errors='ignore') as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            yield line


@contextlib.contextmanager
def get_debconf():
    debconf.runFrontEnd()
    db = debconf.Debconf()
    try:
        yield db
    finally:
        db.stop()


def import_from_string(val):
    module_name, _, attr = val.rpartition('.')
    module = importlib.import_module(module_name)
    return getattr(module, attr)


def assign_variables(string, pairs):
    for k, v in pairs.items():
        v = shlex.quote(v)

        # Add surrounding double quotes if we didn't need to add any above
        v = v if v.startswith("'") else '"{}"'.format(v)

        string = re.sub(
            r'(^|\n)\s*({})=.*'.format(re.escape(k)),
            r'\1\2={}'.format(v),
            string
        )

    return string
