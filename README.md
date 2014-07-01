# paste_capsule

capsule for storing/displaying pastes associated with tags

## install

### app and dependencies
```
git clone https://github.com/tr3buchet/paste_capsule.git
cd paste_capsule
mkdir /opt
mkvirtualenv /opt/paste_capsule
python setup.py install
```

### nginx
```
cp etc/nginx/sites-available/paste_capsule /etc/nginx/sites-available/paste_capsule
# edit server_name in the server block to your host
vi /etc/nginx/sites-available/paste_capsule
ln -s /etc/nginx/sites-available/paste_capsule /etc/nginx/sites-enabled/paste_capsule
```

### systemd gunicorn
```
cp etc/systemd/system/paste_capsule.socket /etc/systemd/system/paste_capsule.socket
cp etc/systemd/system/paste_capsule.service /etc/systemd/system/paste_capsule.service

# edit paste_capsule.service and set the user and group for permissions
vi /etc/systemd/system/paste_capsule.service
```

### redis
make sure `/etc/redis/redis.conf` has a unix socket configured, set perms according to
your desires
```
# check for or set
unixsocket /var/run/redis.sock
unixsocketperm 777
```

### permissions
make sure the user/group you set up in `/etc/systemd/system/paste_capsule.service` has
rwx permissions on `/opt/paste_capsule`
