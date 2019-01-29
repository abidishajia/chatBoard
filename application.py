from flask import Flask, render_template, request, redirect,jsonify, url_for, flash, session as login_session

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Item, User, Base, Post

app = Flask(__name__)

#Connect to Database and create database session
engine = create_engine('sqlite:///chatboard.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Making API Endpoints
@app.route('/chatboard/JSON')
def categoryJSON():
    category = session.query(Category).all()
    return jsonify(Category=[i.serialize for i in category])

@app.route('/chatboard/<int:category_id>/item/JSON')
def categoryItemJSON(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return jsonify(Items=[i.serialize for i in items])

#Main app routes
@app.route('/')
@app.route('/chatboard/')
def showCategories():
    categories = session.query(Category).order_by(asc(Category.name))
    return render_template('categories.html', categories=categories)

@app.route('/chatboard/<int:category_id>')
@app.route('/chatboard/<int:category_id>/item')
def showItems(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    items = session.query(Item).filter_by(category_id = category_id).all()
    return render_template('items.html', items=items, category = category)

@app.route('/chatboard/<int:category_id>/item/newItem', methods=['GET', 'POST'])
def newItem(category_id):
    category = session.query(Category).filter_by(id = category_id).one()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form['description'], category_id=category_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))

    return render_template('newItem.html', category_id=category_id)

@app.route('/chatboard/<int:category_id>/item/<int:item_id>/editItem', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editedItem = session.query(Item).filter_by(id = item_id).first()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    
    return render_template('editItem.html', category_id=category_id, item=editedItem, item_id=item_id)

@app.route('/chatboard/<int:category_id>/item/<int:item_id>/deleteItem', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    category = session.query(Category).filter_by(id = category_id).one()
    itemToDelete = session.query(Item).filter_by(id = item_id).first()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteItem.html', item = itemToDelete, category_id=category_id, item_id=item_id)

@app.route('/chatboard/<int:category_id>/item/<int:item_id>/posts')
def showPosts(category_id, item_id):
    category = session.query(Category).filter_by(id = category_id).one()
    item = session.query(Item).filter_by(category_id = category_id).all()
    posts = session.query(Post).filter_by(item_id = item_id).all()
    return render_template('items.html', item=item, category = category, posts=posts)




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000, threaded = False)
