firstboot
=========

TODO: /usr/bin/gtk3-demo check the applying changes page


----------------------
Suggested applications
----------------------

 * preload
 * laptop-mode
 * pk-update-icon

Reducing writes
---------------

 * Add ``norelatime`` to mount options.

SSD
---

 * Add ``discard`` to mount options.

 * ``cp /usr/share/doc/util-linux/examples/fstrim.{service,timer} /etc/systemd/system``

 * ``systemctl enable fstrim.timer``

Apparmor
--------

 * ``apt install apparmor apparmor-profiles apprpparmor-utils``

 * ``echo 'GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT apparmor=1 security=apparmor"' \
  > /etc/default/grub.d/apparmor.cfg``

 * ``update-grub``

ufw
---

 * ``apt install ufw``
 * ``ufw enable``
