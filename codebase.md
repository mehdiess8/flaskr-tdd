# test.db

This is a binary file of the type: Binary

# requirements.txt

```txt
��b l i n k e r = = 1 . 8 . 2  
 c l i c k = = 8 . 1 . 7  
 c o l o r a m a = = 0 . 4 . 6  
 F l a s k = = 3 . 0 . 3  
 F l a s k - S Q L A l c h e m y = = 3 . 1 . 1  
 g r e e n l e t = = 3 . 1 . 1  
 g u n i c o r n = = 2 3 . 0 . 0  
 i n i c o n f i g = = 2 . 0 . 0  
 i t s d a n g e r o u s = = 2 . 2 . 0  
 J i n j a 2 = = 3 . 1 . 4  
 M a r k u p S a f e = = 2 . 1 . 5  
 p a c k a g i n g = = 2 4 . 1  
 p l u g g y = = 1 . 5 . 0  
 p s y c o p g 2 - b i n a r y = = 2 . 9 . 9  
 p y t e s t = = 8 . 3 . 3  
 S Q L A l c h e m y = = 2 . 0 . 3 5  
 t y p i n g _ e x t e n s i o n s = = 4 . 1 2 . 2  
 W e r k z e u g = = 3 . 0 . 4  
 
```

# flaskr.db

This is a binary file of the type: Binary

# create_db.py

```py
# create_db.py


from project.app import app, db
from project.models import Post


with app.app_context():
    # create the database and the db table
    db.create_all()

    # commit the changes
    db.session.commit()
```

# tests\__init__.py

```py

```

# tests\app_test.py

```py
import os
import pytest
import json
from pathlib import Path

from project.app import app, db

TEST_DB = "test.db"


@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()  # setup
        yield app.test_client()  # tests run here
        db.drop_all()  # teardown


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """initial test. ensure that the database exists"""
    tester = Path("test.db").is_file()
    assert tester


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data

def test_delete_message(client):
    """Ensure the messages are being deleted"""
    rv = client.get('/delete/1')
    data = json.loads(rv.data)
    assert data["status"] == 1
```

# project\__init__.py

```py

```

# project\models.py

```py
from project.app import db


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)

    def __init__(self, title, text):
        self.title = title
        self.text = text

    def __repr__(self):
        return f'<title {self.title}>'
```

# project\app.py

```py
import sqlite3
from pathlib import Path

from flask import Flask, g, render_template, request, session, \
                  flash, redirect, url_for, abort, jsonify
from flask_sqlalchemy import SQLAlchemy


basedir = Path(__file__).resolve().parent

# configuration
DATABASE = "flaskr.db"
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = "thisismysecretkeythatyouwillneverguessbecausethewordisMessi"
#SQLALCHEMY_DATABASE_URI = f'sqlite:///{Path(basedir).joinpath(DATABASE)}'
#{Path(basedir).joinpath(DATABASE)}
SQLALCHEMY_TRACK_MODIFICATIONS = False
BASE_DIR = Path(__file__).resolve().parent.parent
FLASKR_DB = "flaskr.db"


# create and initialize a new Flask app
app = Flask(__name__)
# load the config
#app.config.from_object(__name__)
app.config["DATABASE"] = BASE_DIR.joinpath(FLASKR_DB)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(FLASKR_DB)}"
# init sqlalchemy
db = SQLAlchemy(app)

from project import models


@app.route('/')
def index():
    """Searches the database for entries, then displays them."""
    entries = db.session.query(models.Post)
    return render_template('index.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    """Adds new post to the database."""
    if not session.get('logged_in'):
        abort(401)
    new_entry = models.Post(request.form['title'], request.form['text'])
    db.session.add(new_entry)
    db.session.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login/authentication/session management."""
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('index'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """User logout/authentication/session management."""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('index'))


@app.route('/delete/<int:post_id>', methods=['GET'])
def delete_entry(post_id):
    """Deletes post from database."""
    result = {'status': 0, 'message': 'Error'}
    try:
        db.session.query(models.Post).filter_by(id=post_id).delete()
        db.session.commit()
        result = {'status': 1, 'message': "Post Deleted"}
        flash('The entry was deleted.')
    except Exception as e:
        result = {'status': 0, 'message': repr(e)}
    return jsonify(result)


if __name__ == "__main__":
    app.run()
```

# instance\flaskr.db

```db

```

# .pytest_cache\README.md

```md
# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.

```

# .pytest_cache\CACHEDIR.TAG

```TAG
Signature: 8a477f597d28d172789f06886806bc55
# This file is a cache directory tag created by pytest.
# For information about cache directory tags, see:
#	https://bford.info/cachedir/spec.html

```

# .pytest_cache\.gitignore

```
# Created by pytest automatically.
*

```

# project\templates\login.html

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Flaskr-TDD | Login</title>
    <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
    />
  </head>
  <body>
    <div class="container">
      <br /><br />
      <h1>Flaskr</h1>
      <br /><br />

      {% for message in get_flashed_messages() %}
      <div class="flash alert alert-success col-sm-4" role="success">
        {{ message }}
      </div>
      {% endfor %}

      <h3>Login</h3>

      {% if error %}
      <p class="alert alert-danger col-sm-4" role="danger">
        <strong>Error:</strong> {{ error }}
      </p>
      {% endif %}

      <form action="{{ url_for('login') }}" method="post" class="form-group">
        <dl>
          <dt>Username:</dt>
          <dd>
            <input
              type="text"
              name="username"
              class="form-control col-sm-4"
            />
          </dd>
          <dt>Password:</dt>
          <dd>
            <input
              type="password"
              name="password"
              class="form-control col-sm-4"
            />
          </dd>
          <br /><br />
          <dd>
            <input type="submit" class="btn btn-primary" value="Login" />
          </dd>
          <span>Use "admin" for username and password</span>
        </dl>
      </form>
    </div>
    <script
      type="text/javascript"
      src="{{url_for('static', filename='main.js') }}"
    ></script>
  </body>
</html>
```

# project\templates\index.html

```html
<!DOCTYPE html>
<html>
  <head>
    <title>Flaskr</title>
    <link
      rel="stylesheet"
      type="text/css"
      href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css"
    />
  </head>
  <body>
    <div class="container">
      <br /><br />
      <h1>Flaskr</h1>
      <br /><br />

      {% if not session.logged_in %}
      <a class="btn btn-success" role="button" href="{{ url_for('login') }}"
        >log in</a
      >
      {% else %}
      <a class="btn btn-warning" role="button" href="{{ url_for('logout') }}"
        >log out</a
      >
      {% endif %}

      <br /><br />

      {% for message in get_flashed_messages() %}
      <div class="flash alert alert-success col-sm-4" role="success">
        {{ message }}
      </div>
      {% endfor %} {% if session.logged_in %}
      <form
        action="{{ url_for('add_entry') }}"
        method="post"
        class="add-entry form-group"
      >
        <dl>
          <dt>Title:</dt>
          <dd>
            <input
              type="text"
              size="30"
              name="title"
              class="form-control col-sm-4"
            />
          </dd>
          <dt>Text:</dt>
          <dd>
            <textarea
              name="text"
              rows="5"
              cols="40"
              class="form-control col-sm-4"
            ></textarea>
          </dd>
          <br /><br />
          <dd>
            <input type="submit" class="btn btn-primary" value="Share" />
          </dd>
        </dl>
      </form>
      {% endif %}

      <br />

      <ul class="entries">
        {% for entry in entries %}
        <li class="entry">
          <h2 id="{{ entry.id }}">{{ entry.title }}</h2>
          {{ entry.text|safe }}
        </li>
        {% else %}
        <li><em>No entries yet. Add some!</em></li>
        {% endfor %}
      </ul>
    </div>
    <script
      type="text/javascript"
      src="{{url_for('static', filename='main.js') }}"
    ></script>
  </body>
</html>
```

# project\static\style.css

```css
body {
    font-family: sans-serif;
    background: #eee;
  }
  
  a,
  h1,
  h2 {
    color: #377ba8;
  }
  
  h1,
  h2 {
    font-family: "Georgia", serif;
    margin: 0;
  }
  
  h1 {
    border-bottom: 2px solid #eee;
  }
  
  h2 {
    font-size: 1.2em;
  }
  
  .page {
    margin: 2em auto;
    width: 35em;
    border: 5px solid #ccc;
    padding: 0.8em;
    background: white;
  }
  
  .entries {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  
  .entries li {
    margin: 0.8em 1.2em;
  }
  
  .entries li h2 {
    margin-left: -1em;
  }
  
  .add-entry {
    font-size: 0.9em;
    border-bottom: 1px solid #ccc;
  }
  
  .add-entry dl {
    font-weight: bold;
  }
  
  .metanav {
    text-align: right;
    font-size: 0.8em;
    padding: 0.3em;
    margin-bottom: 1em;
    background: #fafafa;
  }
  
  .flash {
    background: #cee5f5;
    padding: 0.5em;
    border: 1px solid #aacbe2;
  }
  
  .error {
    background: #f0d6d6;
    padding: 0.5em;
  }
```

# project\static\main.js

```js
(function () {
    console.log("ready!"); // sanity check
  })();
  
  const postElements = document.getElementsByClassName("entry");
  
  for (var i = 0; i < postElements.length; i++) {
    postElements[i].addEventListener("click", function () {
      const postId = this.getElementsByTagName("h2")[0].getAttribute("id");
      const node = this;
      fetch(`/delete/${postId}`)
        .then(function (resp) {
          return resp.json();
        })
        .then(function (result) {
          if (result.status === 1) {
            node.parentNode.removeChild(node);
            console.log(result);
          }
          location.reload();
        })
        .catch(function (err) {
          console.log(err);
        });
    });
  }
```

# .pytest_cache\v\cache\stepwise

```
[]
```

# .pytest_cache\v\cache\nodeids

```
[
  "tests/app_test.py::test_database",
  "tests/app_test.py::test_delete_message",
  "tests/app_test.py::test_empty_db",
  "tests/app_test.py::test_index",
  "tests/app_test.py::test_login_logout",
  "tests/app_test.py::test_messages"
]
```

# .pytest_cache\v\cache\lastfailed

```
{}
```

