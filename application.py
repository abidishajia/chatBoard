from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, session as login_session
import random
import string
from functools import wraps
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base, Post

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///chatboard.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
                   json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;"'
    output += ' "-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/gdisconnect')
def gdisconnect():
    categories = session.query(Category).order_by(asc(Category.name))
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
                   json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s'\
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('showCategories', categories=categories))
    else:
        response = make_response(
                json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Making API Endpoints
@app.route('/chatboard/JSON')
def categoryJSON():
    category = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in category])


@app.route('/chatboard/<int:category_id>/JSON')
def categoryOneJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).all()
    return jsonify(Category=[i.serialize for i in category])


@app.route('/chatboard/<int:category_id>/item/JSON')
def categoryItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/JSON')
def categoryItemJSON(category_id, item_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    item = session.query(Item).filter_by(id=item_id).all()
    return jsonify(Items=[i.serialize for i in item])


# Main app routes
@app.route('/')
@app.route('/chatboard/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories)


@app.route('/chatboard/<int:category_id>')
@app.route('/chatboard/<int:category_id>/item')
def showItems(category_id):
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()

    # creator = getUserInfo(category.user_id)
    return render_template(
                'items.html',
                items=items,
                category=category,
                categories=categories,
                category_id=category_id,
               )


@app.route('/chatboard/<int:category_id>/item/newItem',
           methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       category_id=category_id,
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("created a new item")
        return redirect(url_for('showItems', category_id=category_id))

    return render_template(
        'newItem.html',
        category_id=category_id,
        categories=categories)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/editItem',
           methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')

    categories = session.query(Category).order_by(asc(Category.name))
    editedItem = session.query(Item).filter_by(id=item_id).first()

    creator = getUserInfo(editedItem.user_id)

    if creator.id != login_session['user_id']:
        flash("Only the owner can edit this item.")
        return redirect(url_for('showItems', category_id=category_id))

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for(
                'showItems',
                category_id=category_id,
                categories=categories))

    return render_template(
            'editItem.html',
            category_id=category_id,
            item=editedItem,
            item_id=item_id,
            categories=categories)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/deleteItem',
           methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    itemToDelete = session.query(Item).filter_by(id=item_id).first()

    creator = getUserInfo(itemToDelete.user_id)
    if creator.id != login_session['user_id']:
        flash("Only the owner can delete this item.")
        return redirect(url_for('showItems', category_id=category_id))
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template(
            'deleteItem.html',
            item=itemToDelete,
            category_id=category_id,
            item_id=item_id,
            categories=categories)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/posts')
def showPosts(category_id, item_id):
    categories = session.query(Category).order_by(asc(Category.name))
    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(category_id=category_id).all()
    posts = session.query(Post).filter_by(item_id=item_id).all()
    return render_template(
        'posts.html',
        item=item,
        category=category,
        posts=posts,
        categories=categories,
        item_id=item_id,
        category_id=category_id)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/posts/newPost',
           methods=['GET', 'POST'])
def newPost(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))
    item = session.query(Item).filter_by(category_id=category_id).first()

    if request.method == 'POST':
        newPost = Post(post=request.form['post'],
                       item_id=item_id,
                       user_id=login_session['user_id'])
        session.add(newPost)
        session.commit()
        print('USER ID: ', login_session['user_id'])
        return redirect(url_for(
            'showPosts',
            category_id=category_id,
            item_id=item_id))

    return render_template(
            'newPost.html',
            category_id=category_id,
            categories=categories,
            item_id=item_id,
            item=item)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/posts/editPost',
           methods=['GET', 'POST'])
def editPost(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')

    categories = session.query(Category).order_by(asc(Category.name))
    editedPost = session.query(Post).filter_by(id=item_id).first()

    # creator = getUserInfo(editedPost.user_id)
    # if creator.id != login_session['user_id']:
    #     flash ("Only the owner can edit this item.)
    #     return redirect(url_for('showPosts',
    #     category_id=category_id,item_id=item_id))

    if request.method == 'POST':
        if request.form['post']:
            editedPost.post = request.form['post']
        session.add(editedPost)
        session.commit()
        return redirect(url_for(
            'showPosts',
            category_id=category_id,
            item_id=item_id,
            categories=categories))

    return render_template(
            'editPost.html',
            category_id=category_id,
            post=editedPost,
            item_id=item_id,
            categories=categories)


@app.route('/chatboard/<int:category_id>/item/<int:item_id>/posts/deletePost',
           methods=['GET', 'POST'])
def deletePost(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Category).order_by(asc(Category.name))

    category = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id).first()
    postToDelete = session.query(Post).filter_by(id=item_id).first()

    creator = getUserInfo(postToDelete.user_id)
    if creator.id != login_session['user_id']:
        return redirect('/login')

    if request.method == 'POST':
        session.delete(postToDelete)
        session.commit()
        return redirect(url_for(
            'showPosts',
            category_id=category_id,
            item_id=item_id))
    else:
        return render_template(
            'deletePost.html',
            item=postToDelete,
            category_id=category_id,
            item_id=item_id,
            categories=categories)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded=False)
