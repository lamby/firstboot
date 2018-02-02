import os
import grp
import shlex
import logging
import subprocess

from .utils import get_debconf, assign_variables, find_data, find_hooks

logger = logging.getLogger(__name__)


class ApplyData(object):
    def __init__(self, no_act):
        super().__init__()

        self.tzmap = {}
        self.no_act = no_act
        self.groups = {'sudo'}
        self.backups = {}
        self.home_existed = True
        self.debconf_backups = {}

        # Create our Debconf instances outside of a the GTK UI thread.
        logger.info("Getting default user groups from debconf")
        with get_debconf() as db:
            self.groups.update(db.get('passwd/user-default-groups').split(' '))

    def apply(self, data):
        logger.info("Going to apply data: %r", data)

        try:
            self._apply(data)
        except Exception:
            logger.exception("Exception caught whilst applying settings:")
            self.cleanup(data)
            raise

        self.execute(('/bin/run-parts', find_hooks('post-apply.d')))

    def _apply(self, data):
        self.home_existed = os.path.exists('/home/{username}'.format(**data))

        # User
        self.execute((
            'adduser',
            '--disabled-password',
            '--gecos', data['full_name'],
            data['username'],
        ))

        self.execute(
            ('chpasswd',),
            stdin='{username}:{password}'.format(**data).encode('utf-8'),
        )

        all_groups = {x.gr_name for x in grp.getgrall()}
        for x in self.groups:
            if x not in all_groups:
                continue

            self.execute(('adduser', data['username'], x))

        cmd = '/bin/run-parts {}'.format(find_hooks('first-login.d'))

        with open(find_data('firstboot.desktop')) as f:
            self.overwrite_file(
                '/home/{username}/.config/autostart/firstboot.desktop'
                .format(**data),
                f.read().replace('@CMD@', cmd),
                allow_missing=True,
            )

        # Set permissions
        self.execute((
            'chown',
            '-R',
            '{username}:{username}'.format(**data),
            '/home/{username}'.format(**data),
        ))

        # Hosts
        with open('/etc/hosts') as f:
            etc_hosts = f.read()

        with open('/etc/hostname') as f:
            hostname, _, domain = f.read().strip().partition('.')

        # If we had an existing hostname like "example.domain", we need to
        # replace that first
        if domain:
            etc_hosts = etc_hosts.replace(
                '{}.{}'.format(hostname, domain),
                data['hostname'],
            )

        # ... then replace all other instances.
        etc_hosts = etc_hosts.replace(hostname, data['hostname'])

        self.overwrite_file('/etc/hosts', etc_hosts)
        self.overwrite_file('/etc/hostname', '{}\n'.format(data['hostname']))

        # Keyboard
        with open('/etc/default/keyboard') as f:
            keyboard = f.read()

        self.overwrite_file(
            '/etc/default/keyboard',
            assign_variables(keyboard, {
                'XKBLAYOUT': data['keyboard_layout'],
                'XKBVARIANT': data['keyboard_variant'],
            }),
        )

        # Take a backup of this file by doing no processing
        with open('/etc/default/locale') as f:
            locale = f.read()
        self.overwrite_file('/etc/default/locale', locale)

        # FIXME: "mono countries"; also why assume utf-8?
        # eg. LANG="en_GB.UTF-8"
        lang = '{language}_{country}.UTF-8'.format(**data)

        if '_' in data['language']:
            # Don't specify the country if we already have one (eg. zh_TW)
            lang = '{language}.UTF-8'.format(**data)

        # eg. LANGUAGE=en_GB:en
        language = '{language}_{country}:{language}'.format(**data)

        self.execute((
            'update-locale',
            'LANG={}'.format(shlex.quote(lang)),
            'LANGUAGE={}'.format(shlex.quote(language)),
        ))

        # Set timezone

        area, _, zone = data['timezone'].partition('/')

        self.execute(
            'echo tzdata tzdata/Areas select {0} | debconf-set-selections'
            .format(area, zone), shell=True)
        self.execute(
            'echo tzdata tzdata/Zones/{0} select {1} | debconf-set-selections'
            .format(area, zone), shell=True)
        self.execute(('dpkg-reconfigure', '-pcritical', 'tzdata'))

    def cleanup(self, data):
        logger.warning("Cleaning up %r", data)

        self.execute(('deluser', data['username']))
        self.db_set(self.debconf_backups)

        if not self.home_existed:
            self.execute(('rm', '-rf', '/home/{username}'.format(**data)))

        for filename, contents in self.backups.items():
            logger.info('Restoring %s with:', filename)
            for x in contents.splitlines():
                logger.info(x)

            if self.no_act:
                continue

            with open(filename, 'w') as f:
                f.write(contents)

    def execute(self, cmd, stdin=None, *args, **kwargs):
        cmd_fmt = '"{}"'.format(cmd) \
            if isinstance(cmd, str) else ' '.join(shlex.quote(x) for x in cmd)

        if stdin is None:
            logger.info("Calling %s", cmd_fmt)
        else:
            kwargs['stdin'] = subprocess.PIPE
            logger.info("Piping %r to %s", stdin, cmd_fmt)

        if self.no_act:
            return

        with subprocess.Popen(cmd, **kwargs) as p:
            if stdin is not None:
                p.communicate(input=stdin)
            retcode = p.wait()

        if retcode:
            raise subprocess.CalledProcessError(retcode, cmd_fmt)

    def overwrite_file(self, filename, contents, allow_missing=False):
        logger.info("Overwriting %s with:", filename)
        for x in contents.splitlines():
            logger.info("  %s", x)

        if allow_missing and not os.path.exists(filename):
            logger.debug("Ignoring missing target %s", filename)
        else:
            with open(filename, 'r') as f:
                self.backups[filename] = f.read()

        if self.no_act:
            return

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as f:
            f.write(contents)

    def db_set(self, data):
        with get_debconf() as db:
            self.debconf_backups[k] = db.get(k)
            # self.debconf_backups[k] = db.get(k)
            logger.info(
                "Setting debconf value %r -> %r (was: %r",
                k, v, self.debconf_backups[k],
            )
            db.set(k, v)
