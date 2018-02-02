export LANG="en_US.UTF-8"
export LANGUAGE="en_US:en"

/usr/bin/feh --bg-fill /usr/share/firstboot/data/wallpaper.png

xset s off
xsetroot -cursor_name arrow
xbacklight -set 100

exec /usr/lib/firstboot/firstboot
