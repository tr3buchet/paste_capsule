# paste capsule

capsule for storing/displaying pastes associated with tags. it is built in flask
and i included configs for using gunicorn and nginx for deploy. the backend is redis,
which doesn't necessarily make a whole lot of sense, but i like redis and wanted
to play around

## dependencies
* flask
* redis
* nginx
* gunicorn (and and i used gevent)

## install

### app and dependencies
```
git clone https://github.com/tr3buchet/paste_capsule.git
cd paste_capsule
mkdir /opt
mkvirtualenv /opt/paste_capsule
python setup.py install
```

### host configuration
add the following to `/etc/paste_capsule.conf` but set your own hostname
```
[paste_capsule]
hostname = host.name.com
```

### nginx
```
cp etc/nginx/sites-available/paste_capsule /etc/nginx/sites-available/paste_capsule
# edit server_name in the server block to the hostname set in /etc/paste_capsule.conf
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
there are plenty of guides out there for installing [redis](http://redis.io).
the app is configured to connect to redis using a unix socket, so maake sure
`/etc/redis/redis.conf` has a unix socket configured, set perms according to
your desires
```
# check for or set
unixsocket /run/redis.sock
unixsocketperm 777
```

### permissions
make sure the user/group you set up in `/etc/systemd/system/paste_capsule.service` has
rwx permissions on `/opt/paste_capsule`