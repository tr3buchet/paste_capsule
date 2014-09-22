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

### mysql
```
sudo apt-get install mysql-server mysql-client libmysqlclient-dev

# enable some utf8 goodness
cp etc/mysql/conf.d/utf8.cnf /etc/mysql/conf.d/utf8.cnf
systemctl restart mysql
# double check my running the following
mysql> show variables like 'char%';
+--------------------------+----------------------------+
| Variable_name            | Value                      |
+--------------------------+----------------------------+
| character_set_client     | utf8                       |
| character_set_connection | utf8                       |
| character_set_database   | utf8                       |
| character_set_filesystem | binary                     |
| character_set_results    | utf8                       |
| character_set_server     | utf8                       |
| character_set_system     | utf8                       |
| character_sets_dir       | /usr/share/mysql/charsets/ |
+--------------------------+----------------------------+
8 rows in set (0.00 sec)

mysql> show variables like 'collation%';
+----------------------+-----------------+
| Variable_name        | Value           |
+----------------------+-----------------+
| collation_connection | utf8_general_ci |
| collation_database   | utf8_unicode_ci |
| collation_server     | utf8_unicode_ci |
+----------------------+-----------------+
3 rows in set (0.00 sec)

# create user permissions for app sql user
mysql -u root -p
CREATE USER 'username'@'localhost' IDENTIFIED BY 'password';

GRANT ALL ON paste_capsule . * TO 'username'@'localhost';

FLUSH PRIVILEGES;

# create paste_capsule database, app creates the tables automatically
create database paste_capsule
exit
```

### tmpfiles.d
```
# add the tmpfiles config and create the actual directory
cp etc/tmpfiles.d/paste_capsule.conf /etc/tmpfiles.d/paste_capsule.conf
systemd-tmpfiles --create /etc/tmpfiles.d/paste_capsule.conf
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
# also set the PASTE_CAPSULE_DATABASE to your sql database connection with user/pass from sql user
vi /etc/systemd/system/paste_capsule.service

# enable and start the socket
systemctl enable paste_capsule.socket
systemctl start paste_capsule.socket
```

### permissions
make sure the user/group you set up in `/etc/systemd/system/paste_capsule.service` has
rwx permissions on `/opt/paste_capsule`
