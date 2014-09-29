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
import datetime

import flask
import flask_appconfig
import flask_bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy import func
from sqlalchemy import desc

db = SQLAlchemy()


class Paste(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(255), index=True, nullable=False)
    text = db.Column(LONGTEXT, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, tag, text, created_at=None):
        self.tag = tag
        self.text = text
        if created_at is None:
            self.created_at = datetime.datetime.utcnow()


highlights = ['BOOM']
highlight_color = 'pink'


def tag_index():
    q = db.session.query
    tags = q(Paste.tag, func.count(Paste.id)).group_by(Paste.tag).\
        order_by(Paste.tag).all()
    num_pastes = q(func.count(Paste.id)).first()[0] if tags else 0
    return flask.render_template('tag_index.html', tags=tags,
                                 num_pastes=num_pastes)


def tag_show(tag):
    pastes = Paste.query.filter(Paste.tag == tag).\
        order_by(desc(Paste.created_at)).all()
    if not pastes:
        return 'tag not found'
    # NOTE(tr3buchet): get the highlights
    highlight_list = [highlight(p.text) for p in pastes]
    pastes = [(p, hl) for p, hl in zip(pastes, highlight_list)]

    return flask.render_template('tag_show.html', tag=tag,
                                 pastes=pastes)


def highlight(paste):
    for h in highlights:
        if h in paste:
            return 'highlight'
    return ''


def paste_create():
    params = flask.request.get_json()
    p = Paste(tag=params.get('tag', 'no-tag'), text=params['data'])
    db.session.add(p)
    db.session.commit()

    return url() + flask.url_for('paste_show', paste_id=p.id)


def paste_show(paste_id):
    p = Paste.query.get(paste_id)
    return flask.render_template('paste_show.html', paste=p)
#    return flask.Response(p.text, mimetype='text/plain')


def paste_show_raw(paste_id):
    p = Paste.query.get(paste_id)
    return flask.Response(p.text, mimetype='text/plain')


def delete_paste(paste_id):
    Paste.query.get(paste_id).delete()
    return '|%s| deleted' % paste_id


def linky(resource, s, **kwargs):
    return '<a href="%s%s">%s</a>' % (url(),
                                      flask.url_for(resource, **kwargs), s)


def url():
    app = flask.current_app
    try:
        return 'http://%s' % app.config['HOSTNAME']
    except:
        return 'http://127.0.0.1:8000'


def create_app(debug=False, *args, **kwargs):
    app = flask.Flask('paste_capsule')
    app.debug = debug
    flask_appconfig.AppConfig(app)
    flask_bootstrap.Bootstrap(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.context_processor
    def utility_processor():
        def htime(ts):
            return ts.strftime('%a %d %b %Y %H:%M:%S %Z')
        return dict(htime=htime)

    app.add_url_rule('/', 'tag_index', tag_index, methods=['get'])
    app.add_url_rule('/tag/<tag>', 'tag_show', tag_show, methods=['get'])
    app.add_url_rule('/paste', 'paste_create', paste_create, methods=['post'])
    app.add_url_rule('/paste/<paste_id>', 'paste_show',
                     paste_show, methods=['get'])
    app.add_url_rule('/paste/<paste_id>/raw', 'paste_show_raw',
                     paste_show_raw, methods=['get'])
    app.add_url_rule('/paste/<paste_id>', 'delete_paste', delete_paste,
                     methods=['delete'])
    return app


if __name__ == '__main__':
    create_app().run(debug=True, host='127.0.0.1', port=8000)
