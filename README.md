# paste capsule

capsule for storing/displaying pastes associated with tags. it is built in flask
and i included configs for using gunicorn and nginx for deploy. the backend is now
mysql which makes way more sense than redis for storing pastes

## dependencies
* flask
* mysql
* nginx
* gunicorn (and and i used gevent)

## install

### app and dependencies
substitute `virtualenv` for `mkvirtualenv` below if not using virtualenv wrapper.
depending on your user and permissions you may have to `sudo` or do some `chown`ing
```
git clone https://github.com/tr3buchet/paste_capsule.git
cd paste_capsule
mkdir /opt
mkvirtualenv /opt/paste_capsule
. /opt/paste_capsule/bin/activate
python setup.py install
```

### nginx
```
cp etc/nginx/sites-available/paste_capsule /etc/nginx/sites-available/paste_capsule
# edit server_name in the server block to the hostname of the machine
vi /etc/nginx/sites-available/paste_capsule
ln -s /etc/nginx/sites-available/paste_capsule /etc/nginx/sites-enabled/paste_capsule
# reload nginx config
systemctl reload nginx
```

### systemd gunicorn
```
cp etc/systemd/system/paste_capsule.socket /etc/systemd/system/paste_capsule.socket
cp etc/systemd/system/paste_capsule.service /etc/systemd/system/paste_capsule.service

# edit paste_capsule.service and set the user and group for permissions
# also set the PASTE_CAPSULE_HOSTNAME to the same value in the nginx config
vi /etc/systemd/system/paste_capsule.service

# enable and start the socket
systemctl enable paste_capsule.socket
systemctl start paste_capsule.socket
```

### mysql
```
sudo apt-get install mysql-server mysql-client libmysqlclient-dev
mysql -u root -p
CREATE USER 'pc'@'localhost' IDENTIFIED BY 'd0ngs';

GRANT ALL ON paste_capsule . * TO 'pc'@'localhost';

FLUSH PRIVILEGES;
create database paste_capsule
exit
```

### permissions
make sure the user/group you set up in `/etc/systemd/system/paste_capsule.service` has
rwx permissions on `/opt/paste_capsule`
