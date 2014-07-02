#!/usr/bin/env python
#
# Copyright 2014 Trey Morris
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
import redis
import time
import datetime
import shortuuid
import ConfigParser

from flask import Flask
from flask import request
from flask import Response
from flask import url_for

app = Flask(__name__)
app.debug = True

HOST = get_host_config()
URL = 'http://%s' % HOST
#r = redis.StrictRedis(host='localhost', port=6379, db=3)
r = redis.StrictRedis(unix_socket_path='/run/redis.sock', db=3)

###### REDIS SCHEMA ######
# lexicographically sorted set of tags
#    tags
# time sorted set of paste uuids with tag
#    tag:<tagname>
# time sorted set of pastes (for sorting in tag view and reaping later)
#    pastes
# paste -> tag map for each paste (for reaping from tag:<tagname>)
#    paste_tag:<uuid>
# each paste
#    paste:<uuid>


def get_host_config():
    config_parser = ConfigParser.RawConfigParser(
        defaults={'hostname': 'host.name.com'})
    # read from ~/.gister if it exists else use defaults
    if not config_parser.read('/etc/paste_capsule.conf'):
        raise Exception('could not read hostname from /etc/paste_capsule.conf')
    return config_parser.get('paste_capsule', 'hostname')


@app.route('/', methods=['get'])
def index():
    with r.pipeline() as pipe:
        pipe.zrange('tags', 0, -1)
        pipe.zcard('tags')
        tag_list, num_tags = pipe.execute()
    if not num_tags:
        return 'no tags found'
    urls = [linky('tag', tag, tagname=tag) for tag in tag_list]
    return '%s tags:<br>\n%s' % (num_tags, '<br>\n'.join(urls))


@app.route('/tag/<tagname>', methods=['get'])
def tag(tagname):
    paste_uuid_list = r.zrange('tag:%s' % tagname, 0, -1)
    if not paste_uuid_list:
        return 'tag not found'
    with r.pipeline() as pipe:
        ts_list = []
        for paste_uuid in paste_uuid_list:
            pipe.zscore('pastes', paste_uuid)
        ts_list = pipe.execute()
    urls = [linky('paste', '%s - %s' % (htime(ts), paste_uuid),
                  paste_uuid=paste_uuid)
            for paste_uuid, ts in zip(paste_uuid_list, ts_list)]
    return '%s pastes for %s:<br>\n%s' % (len(ts_list), tagname,
                                          '<br>\n'.join(urls))


@app.route('/paste/<paste_uuid>', methods=['get'])
def paste(paste_uuid):
    p = r.get('paste:%s' % paste_uuid)
    return Response(p, mimetype='text/plain')


@app.route('/', methods=['post'])
def post():
    params = request.get_json()
    data = params['data']
    tagname = params.get('tag', 'no-tag')
    paste_uuid = shortuuid.uuid()
    ts = time.time()

    with r.pipeline() as pipe:
        # add tagname to lexicographically sorted tags set
        pipe.zadd('tags', 1, tagname)
        # add paste uuid to this tag's time sorted set
        pipe.zadd('tag:%s' % tagname, ts, paste_uuid)
        # add paste uuid to the time sorted pastes set
        pipe.zadd('pastes', ts, paste_uuid)
        # add paste_uuid -> tagname mapping
        pipe.set('paste_tag:%s' % paste_uuid, tagname)
        # add the paste
        pipe.set('paste:%s' % paste_uuid, data)
        pipe.execute()

    return URL + url_for('paste', paste_uuid=paste_uuid)


def linky(resource, s, **kwargs):
    return '<a href="%s%s">%s</a>' % (URL, url_for(resource, **kwargs), s)


def htime(ts):
    return datetime.datetime.fromtimestamp(ts)


@app.route('/delete/<paste_uuid>', methods=['get'])
def delete_paste(paste_uuid):
    # get the tagname info related to this paste_uuid
    tagname = r.get('paste_tag:%s' % paste_uuid)
    num_pastes = r.zcard('tag:%s' % tagname)
    msg = 'delete |%s| with tag |%s| which has |%s| pastes'
    app.logger.debug(msg % (tagname, num_pastes))
    with r.pipeline() as pipe:
        # remove paste_uuid from tag's set of paste_uuids
        pipe.zrem('tag:%s' % tagname, paste_uuid)
        # remove paste_uuid from the time sorted pastes set
        pipe.zrem('pastes', paste_uuid)
        # remove paste_uuid from the paste_uuid -> tagname mapping
        pipe.delete('paste_tag:%s' % paste_uuid)
        # delete the paste itself
        pipe.delete('paste:%s' % paste_uuid)

        # if the tagname no longer has any associated paste,
        # remove it from the tags set
        if num_pastes <= 1:
            pipe.zrem('tags', tagname)
        x = pipe.execute()

    msg = ('remove paste uuid from tag |%s|\n'
           'remove paste uuid from pastes set |%s|\n'
           'remove paste uuid from paste_tag mapping |%s|\n'
           'remove the paste |%s|\n')
    if len(x) == 5:
        msg += 'remove tagname from tags |%s|'
    app.logger.debug(msg % x)
    return '|%s| deleted' % paste_uuid
