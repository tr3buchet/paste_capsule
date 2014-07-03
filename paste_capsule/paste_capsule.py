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

import flask
import flask_appconfig
import flask_bootstrap

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


def tag_index():
    tag_list = r.zrange('tags', 0, -1)
    with r.pipeline() as pipe:
        for tag in tag_list:
            pipe.zcard('tag:%s' % tag)
        tag_num_list = pipe.execute()
    tags = dict(zip(tag_list, tag_num_list))
    return flask.render_template('tag_index.html', tags=tags)


def tag_show(tagname):
    pastes = dict((k, htime(ts))
                  for k, ts in r.zscan('tag:%s' % tagname, 0)[1])
    print pastes
    if not pastes:
        return 'tag not found'
    return flask.render_template('tag_show.html', tagname=tagname,
                                                  pastes=pastes)
    urls = [linky('paste', '%s - %s' % (htime(ts), paste_uuid),
                  paste_uuid=paste_uuid)
            for paste_uuid, ts in zip(paste_uuid_list, ts_list)]
    return '%s pastes for %s:<br>\n%s' % (len(ts_list), tagname,
                                          '<br>\n'.join(urls))


def paste_create():
    params = flask.request.get_json()
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

    return url() + flask.url_for('paste_show', paste_uuid=paste_uuid) + '\n'


def paste_show(paste_uuid):
    p = r.get('paste:%s' % paste_uuid)
    return flask.render_template('paste_show', paste=p)
#    return flask.Response(p, mimetype='text/plain')


def delete_paste(paste_uuid):
    # get the tagname info related to this paste_uuid
    tagname = r.get('paste_tag:%s' % paste_uuid)
    num_pastes = r.zcard('tag:%s' % tagname)
    msg = 'delete |%s| with tag |%s| which has |%s| pastes'
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
    return '|%s| deleted' % paste_uuid


def linky(resource, s, **kwargs):
    return '<a href="%s%s">%s</a>' % (url(),
                                      flask.url_for(resource, **kwargs), s)


def htime(ts):
    return datetime.datetime.fromtimestamp(ts)


def url():
    app = flask.current_app
    try:
        return 'http://%s' % app.config['HOSTNAME']
    except:
        return 'http://127.0.0.1:8000'


def create_app(*args, **kwargs):
    app = flask.Flask('paste_capsule')
    flask_appconfig.AppConfig(app)
    flask_bootstrap.Bootstrap(app)

    app.add_url_rule('/', 'tag_index', tag_index, methods=['get'])
    app.add_url_rule('/tag/<tagname>', 'tag_show', tag_show, methods=['get'])
    app.add_url_rule('/paste', 'paste_create', paste_create, methods=['post'])
    app.add_url_rule('/paste/<paste_uuid>', 'paste_show', paste_show,
                     methods=['get'])
    app.add_url_rule('/paste/<paste_uuid>', 'delete_paste', delete_paste,
                     methods=['delete'])

    return app


if __name__ == '__main__':
    create_app().run(debug=True, host='127.0.0.1', port=8000)
