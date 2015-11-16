from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import bleach
from markdown import markdown
from flask import current_app

from flask.ext.login import UserMixin
from . import db, login_manager


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    bugs = db.relationship('Bugs', backref='author', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Bugs(db.Model):
    __tablename__ = 'bugs'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    product_name = db.Column(db.String(64))
    product_version = db.Column(db.String(64))
    software_version = db.Column(db.String(64))
    bug_level = db.Column(db.String(64))
    system_view = db.Column(db.String(64))
    bug_show_times = db.Column(db.String(64))
    bug_title = db.Column(db.String(64))
    bug_descrit = db.Column(db.Text)
    bug_owner_id = db.Column(db.String(64))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    # comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.id

    @staticmethod
    def on_changed_bug_descrit(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Bugs.bug_descrit, 'set', Bugs.on_changed_bug_descrit)