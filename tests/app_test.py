import os
import pytest
import json
from pathlib import Path

from project.app import app, db
from project import models

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
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 1

def test_search(client):
    # Log in using the helper function
    login(client, 'admin', 'admin')

    # Add a test entry using the existing '/add' route
    client.post(
        '/add',
        data=dict(title="Testing search post", text="This is a test post"),
        follow_redirects=True
    )

    # Verify that the post exists in the database
    post = models.Post.query.filter_by(title="Testing search post").first()
    assert post is not None, "Post wasn't added to the database"

    # Perform the search
    response = client.get('/search', query_string={'query': 'test'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Testing search post' in response.data
    assert b'This is a test post' in response.data

def test_delete_requires_login(client):
    # Log in using the helper function and add a test entry using the existing '/add' route
    login(client, 'admin', 'admin')
    client.post('/add', data={'title': 'Post to Delete', 'text': 'This post will be deleted'}, follow_redirects=True)

    # Verify that the post exists in the database
    post = models.Post.query.filter_by(title="Post to Delete").first()
    assert post is not None, "Post wasn't added to the database"
    
    post_id = post.id

    # Log out the user using the logout helper function
    logout(client)

    # Attempt to delete the post without being logged in
    response = client.get(f'/delete/{post_id}', follow_redirects=True)
    assert response.status_code == 401 or b'You need to log in' in response.data  

    # Log in and try to delete the post
    login(client, 'admin', 'admin')
    response = client.get(f'/delete/{post_id}', follow_redirects=True)

    # Check that the deletion was successful
    assert response.status_code == 200
    assert models.Post.query.filter_by(id=post_id).first() is None, "Post was not deleted"



