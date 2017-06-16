from flask import Flask, render_template, request
from flask import redirect, jsonify, url_for, flash

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Category Menu Application"


# Connect to Database and create database session
engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def showLogin():
    """
    Create anti-forgery state token
    and render the login interface for users
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Google login
    1. Validate the anti-forgery state token generated above
    2. Obtain authorization code and Upgrade the authorization code
    into a credentials object(access token)
    3. Handle cases like 'invalid token'.
    4. Get user info and check if it exists, if it doesn't make a new one.
    """
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
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
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
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
              -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Revoke a current user's token and reset their login_session.
    """
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash('Successfully disconnected.')
        return redirect(url_for('showCategories'))

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
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
    except:
        return None


# JSON APIs to view Category Information
@app.route('/category/<int:category_id>/items/JSON')
def categoryItemsJSON(category_id):
    """
    to show the items info of a specific category in JSON format
    """
    items = session.query(Item).filter_by(
        category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/category/<int:category_id>/items/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    """
    to show a specific item in JSON format
    """
    oneItem = session.query(Item).filter_by(id=item_id).one()
    return jsonify(oneItem=oneItem.serialize)


@app.route('/category/JSON')
def categoriesJSON():
    """
    to show all the categories info in JSON format
    """
    categories = session.query(Category).all()
    return jsonify(categories=[r.serialize for r in categories])


@app.route('/')
@app.route('/category/')
def showCategories():
    """
    Show all categories
    if user has logged in, render the interface with functions of edit/delete
    if has not, render the view-only page.
    """
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return render_template('publicCategories.html', categories=categories)
    else:
        return render_template('categories.html', categories=categories)


@app.route('/category/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
    """
    Create a new category
    if user has logged in, enable the user to create a new catogory
    if not, show the user a waring and won't redirect.
    """
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New Category %s Successfully Created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


@app.route('/category/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """
    Edit an existing category
    if user has logged in, enable the user to edit an existing catogory
    if not, show the user a waring and won't redirect.
    """
    try:
        categoryToEdit = session.query(
            Category).filter_by(id=category_id).one()
        if categoryToEdit.user_id != login_session['user_id']:
            flash('''You are not authorized to edit this category.
                  Please create your own category in order to edit.''')
            return redirect(url_for('showCategories'))
        if request.method == 'POST':
            if request.form['name']:
                categoryToEdit.name = request.form['name']
                flash('Category Successfully Edited %s' % categoryToEdit.name)
                return redirect(url_for('showCategories'))
        else:
            return render_template('editCategory.html',
                                   category=categoryToEdit)
    except:
        flash('''Category does not exist!''')
        return redirect(url_for('showCategories'))


@app.route('/category/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    """
    Edit an exsiting category
    if user has logged in, enable the user to delete an existing catogory
    if not, show the user a waring and won't redirect.
    """
    try:
        categoryToDelete = session.query(
            Category).filter_by(id=category_id).one()
        if categoryToDelete.user_id != login_session['user_id']:
            flash('''You are not authorized to delete this category.
                  Please create your own category in order to delete.''')
            return redirect(url_for('showCategories',
                                    category_id=category_id))
        if request.method == 'POST':
            session.delete(categoryToDelete)
            flash('%s Successfully Deleted' % categoryToDelete.name)
            session.commit()
            return redirect(url_for('showCategories',
                                    category_id=category_id))
        else:
            return render_template('deleteCategory.html',
                                   category=categoryToDelete)
    except:
        flash('''Category does not exist!''')
        return redirect(url_for('showCategories'))


# Show a list of items
@app.route('/category/<int:category_id>/')
@app.route('/category/<int:category_id>/items/')
def showItems(category_id):
    """
    Show all items
    if user has logged in, render the interface with functions of edit/delete
    if has not, render the view-only page.
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        creator = getUserInfo(category.user_id)
        items = session.query(Item).filter_by(
            category_id=category_id).all()
        if ('username' not in login_session or
                creator.id != login_session['user_id']):
            return render_template('publicItems.html',
                                   items=items,
                                   category=category,
                                   creator=creator)
        else:
            return render_template('items.html',
                                   items=items,
                                   category=category,
                                   creator=creator)
    except:
        flash('''Category does not exist!''')
        return redirect(url_for('showCategories'))


@app.route('/category/<int:category_id>/items/new/',
           methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    """
    Create a new item
    if user has logged in, enable the user to create a new item
    if not, show the user a waring and won't redirect.
    """
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        if request.method == 'POST':
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           price=request.form['price'],
                           category_id=category_id,
                           user_id=category.user_id)
            session.add(newItem)
            session.commit()
            flash('New Menu %s Item Successfully Created' % (newItem.name))
            return redirect(url_for('showItems', category_id=category_id))
        else:
            return render_template('newItem.html', category_id=category_id)
    except:
        flash('''Category does not exist!''')
        return redirect(url_for('showCategories'))


# Edit an item
@app.route('/category/<int:category_id>/items/<int:item_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    """
    Edit an existing item
    if user has logged in, enable the user to edit an existing item
    if not, show the user a waring and won't redirect.
    """
    try:
        itemToEdit = session.query(Item).filter_by(id=item_id).one()
        if itemToEdit.user_id != login_session['user_id']:
            flash('''You are not authorized to edit this item.
                  Please create your own item in order to edit.''')
            return redirect(url_for('showItems', category_id=category_id))
        if request.method == 'POST':
            if request.form['name']:
                itemToEdit.name = request.form['name']
            if request.form['description']:
                itemToEdit.description = request.form['description']
            if request.form['price']:
                itemToEdit.price = request.form['price']
            session.add(itemToEdit)
            session.commit()
            flash('Menu Item Successfully Edited')
            return redirect(url_for('showItems', category_id=category_id))
        else:
            return render_template('editItem.html',
                                   category_id=category_id,
                                   item_id=item_id,
                                   item=itemToEdit)
    except:
        flash('''Item does not exist!''')
        return redirect(url_for('showItems', category_id=category_id))


# Delete an item
@app.route('/category/<int:category_id>/items/<int:item_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    """
    Delete an existing item
    if user has logged in, enable the user to delete an existing item
    if not, show the user a waring and won't redirect.
    """
    try:
        itemToDelete = session.query(Item).filter_by(id=item_id).one()
        if itemToDelete.user_id != login_session['user_id']:
            flash('''You are not authorized to delete this item.
                  Please create your own item in order to delete.''')
            return redirect(url_for('showItems', category_id=category_id))
        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            flash('Menu Item Successfully Deleted')
            return redirect(url_for('showItems', category_id=category_id))
        else:
            return render_template('deleteItem.html', item=itemToDelete)
    except:
        flash('''Item does not exist!''')
        return redirect(url_for('showItems', category_id=category_id))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
