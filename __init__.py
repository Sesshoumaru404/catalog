import httplib2
import os
import json
import random
import string
import requests
from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash, send_from_directory, make_response
from flask import session as login_session
from flask_wtf.csrf import CsrfProtect
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from sqlalchemy import create_engine, asc, text, inspect
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from catalog import Category, Base, Item, User
from helpers import Pagination, slices

__author__ = 'sesshoumaru404@outlook.com (Paul)'

# Setup different optinon
UPLOAD_FOLDER = '/var/www/CatalogApp/catalog/images'
# GOOGLE_JSON = '/home/{user}/Coding/catalog/client_secrets.json'
GOOGLE_JSON = '/var/www/CatalogApp/catalog/client_secrets.json'
PER_PAGE = 10
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

# Get sercets for Google plus sign in
CLIENT_ID = json.loads(
    open(GOOGLE_JSON, 'r').read())['web']['client_id']
APPLICATION_NAME = "Project 3 Catalog App"
# Config images folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Config max size of image, to increase change fisrt value
# starting value is 2mb
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
# Hide database info use this command in terminal
# echo DATABASE_URL=postgresql://user:password@ipaddress/dbname
# echo DATABASE_URL=postgresql://catalogapp:project5@localhost/catalog

# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(32))
# Csft propect site
CsrfProtect(app)

engine = create_engine("postgresql://sesshoumaru:sesshoumaru@localhost/catalog")
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/feeds')
def catalogJSON():
    """
    An json feed for category and item.
    """
    feed = request.args.get('feed')
    print feed
    if feed == "categories":
        categories = session.query(Category).all()
        return jsonify(categories=[r.serialize for r in categories])
    elif feed == "items":
        items = session.query(Item).all()
        return jsonify(items=[r.serialize for r in items])
    else:
        flash("Page Not Found")
        return page_not_found("404: Not Found")


@app.route('/feeds/ATOM')
def catalogATOM():
    """
    An atom feed for the 15 lastest items.
    """
    items = session.query(Item).limit(15).all()
    feed = AtomFeed('Items Feed', feed_url=request.url, url=request.url_root)

    for c in items:
        feed.add(c.name, c.category.name,
                 id=c.id,
                 url=request.url_root +
                 "catalog/%s" % c.category.name + "?item=%s" % c.id,
                 content_type='html',
                 updated=c.edited_At)
    return feed.get_response()


# Create anti-forgery state token
@app.route('/login', methods=['GET'])
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/connect', methods=['POST'])
def googleConnect():
    # Ensure that the request is not a forgery and that the user sending
    # this connect request is the expected user.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(GOOGLE_JSON, scope='')
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
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    # First User to login gets administrator status
    if session.query(User).first().name == 'admin':
        user = session.query(User).first()
        user.email = data['email']
        user.name = data['name']
        session.add(user)
        session.commit()
        login_session['email'] = user.email
        login_session['name'] = user.name
        login_session['admin'] = user.admin
    else:
        # See if user is a passed user if not create account
        findUser = session.query(User).filter(User.email == data['email'])
        if findUser.first():
            login_session['email'] = findUser.one().email
            login_session['name'] = findUser.one().name
            login_session['admin'] = findUser.one().admin
        else:
            newUser = User(email=data['email'],
                           name=data['name'])
            session.add(newUser)
            session.commit()
            login_session['email'] = newUser.email
            login_session['name'] = newUser.name
            login_session['admin'] = False

    response = make_response(json.dumps('Successfully connected user.'), 200)
    response.headers['Content-Type'] = 'application/json'

    return response


@app.route('/disconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        flash('Current user not connected.')
        return redirect(url_for('showCatalog'))
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['email']
        del login_session['name']
        del login_session['admin']

        flash('Successfully Logout.')
        return redirect(url_for('showCatalog'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Show all Items
@app.route('/')
@app.route('/catalog/<int:page>', methods=['GET'])
@app.route('/catalog/<category_name>/<int:page>', methods=['GET'])
def showCatalog(category_name=None, page=1):
    """ Show all items and show all by category. """
    start, stop = slices(page, PER_PAGE)
    categories = session.query(Category).order_by(Category.name.asc())
    items = session.query(Item).order_by(Item.edited_At.desc())
    category = False
    if category_name:
        if checkCategory(category_name):
            items = session.query(Item).\
                filter(Item.category.has(name=category_name))
            category = category_name
        else:
            return page_not_found("404: Not Found")
    item_list = items.slice(start, stop)
    item_count = items.count()
    pagination = Pagination(page, PER_PAGE, item_count)
    return render_template('index.html', categories=categories,
                           lastest=item_list, pagination=pagination,
                           category=category, item_count=item_count)


# Show an Item
@app.route('/catalog/<category_name>', methods=['GET'])
def showItem(category_name):
    item_id = request.args.get('item')
    if checkCategory(category_name):
        item = session.query(Item).filter(Item.id == item_id).one()
        return render_template('show.html', item=item)
    else:
        return page_not_found("Invaild category")


# Edit a item
@app.route('/catalog/<category_name>/edit', methods=['GET', 'POST'])
def editItem(category_name):
    """ Only a sign-in creator can edit their items. """
    if not userLoggedIn():
        flash('Must be logged in to Edit Item')
        return redirect(url_for('showCatalog'))
    item_id = request.args.get('item')
    categories = session.query(Category).all()
    if checkCategory(category_name):
        if request.method == 'POST':
            editedItem = session.query(Item).filter(Item.id == item_id).one()
            if not matchUser(editedItem.user.email):
                flash('Cannot edit a item you did not create')
                return redirect(url_for('showCatalog'))
            image = request.files['image']
            imagepath = None
            # Code for editing a image and removing a old image
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                filename = unquieName(filename, item_id)
                deletepath = editedItem.image
                imagepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                try:
                    if editedItem.image:
                        os.remove(deletepath)
                    image.save(imagepath)
                    editedItem.image = imagepath
                except Exception as e:
                    os.remove(imagepath)
                    editedItem.image = None
                    flash(e)
                    return redirect(url_for('editItem',
                                    category_name=category_name, item=item_id))
            for attr in request.form:
                if request.form[attr]:
                    if attr == 'image':
                        pass
                    print request.form['category_id']
                    setattr(editedItem, attr, request.form[attr])
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showItem',
                                    category_name=category_name, item=item_id))
        else:
            item = session.query(Item).filter(Item.id == item_id).one()
            return render_template('update.html',
                                   categories=categories, item=item)
    else:
        return page_not_found("404: Not Found")


# Delete a category item
@app.route('/catalog/<category_name>/delete', methods=['GET', 'POST'])
def deleteItem(category_name):
    """
    Only a sign-in creator can delete their items.
    """
    item_id = request.args.get('item')
    itemToDelete = session.query(Item).filter(Item.id == item_id).one()
    if request.method == 'POST':
        if matchUser(itemToDelete.user.email):
            if itemToDelete.image:
                os.remove(itemToDelete.image)
            session.delete(itemToDelete)
            session.commit()
            flash(itemToDelete.name.title() + ' successfully Deleted')
            return redirect(url_for('showCatalog'))
        else:
            flash('Must be logged on and creator to delete')
            return redirect(url_for('showItem',
                                    category_name=category_name, item=item_id))

    return render_template('deleteItem.html', item=itemToDelete)


@app.route('/catalog/item/create', methods=['GET', 'POST'])
def createItem():
    """
    All user can create a new item.
    """
    if not userLoggedIn():
        flash('Must be logged in to Create Item')
        return redirect(url_for('showCatalog'))
    categories = session.query(Category).all()
    if request.method == 'POST':
        user = session.query(User).filter(User.email == login_session['email']).one()
        image = request.files['image']
        imagepath = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filename = unquieName(filename)
            imagepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(imagepath)
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       category_id=request.form['category_id'],
                       user_id=user.id,
                       image=imagepath)
        session.add(newItem)
        session.flush()
        session.commit()
        flash(newItem.name + ' Successfully created')
        return redirect(url_for('showItem',
                                category_name=newItem.category.name,
                                item=newItem.id))
    return render_template('update.html',
                           categories=categories, new=True)


@app.route('/catalog/category/create', methods=['GET', 'POST'])
def createCategory():
    """
    All users can create a new category.
    """
    if not userLoggedIn():
        flash('Must be logged in to create new category')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        name = request.form['name'].lower()
        if session.query(Category).filter(Category.name == name).first():
            flash('Category exist with that name')
            return redirect(url_for('createCategory'))
        category = Category(name=name)
        session.add(category)
        session.commit()
        flash(name.title() + ' successfully created')
        return redirect(url_for('showCatalog'))
    return render_template('updatecategory.html', newCategory=True)


@app.route('/catalog/category/edit', methods=['GET', 'POST'])
def editCategory():
    """
    Edit a category only Administrator are allowed to edit categories.
    """
    if not userAdmin():
        flash('Must be an Administrator to edit a category')
        return redirect(url_for('showCatalog'))
    if request.method == 'POST':
        category_name = request.args.get('name')
        name = request.form['name'].lower()
        editcategory = session.query(Category).filter(Category.name == category_name).one()
        if session.query(Category).filter(Category.name == name).first():
            flash('Category exist with that name')
            return redirect(url_for('editCategory'))
        editcategory.name = name
        session.add(editcategory)
        session.commit()
        flash(name.title() + ' successfully edited')
        return redirect(url_for('showCatalog'))
    category_name = request.args.get('name')
    editcategory = session.query(Category).filter(Category.name == category_name).one()
    return render_template('updatecategory.html', editcategory=editcategory)


@app.route('/catalog/category/delete', methods=['GET', 'POST'])
def deleteCategory():
    """
    Delete a category only user and delete categories and must be an
    Administrator to delete category that still have items a associated
    with that category.
    """
    if not userLoggedIn():
        flash('Must be a user to delete a category')
        return redirect(url_for('showCatalog'))
    category_name = request.args.get('name')
    deleteCat = session.query(Category).filter(Category.name == category_name)
    if request.method == 'POST':
        if deleteCat.first().items != [] and not userAdmin():
            flash('Must be an Administrator to erase a non empty category')
            return redirect(url_for('showCatalog'))
        else:
            # Remove all associated item and items
            remove_items = session.query(Item).filter(Item.category.has(name=category_name))
            for item in remove_items:
                if item.image:
                    os.remove(item.image)
                session.delete(item)
        session.delete(deleteCat.first())
        session.commit()
        flash(category_name.title() + ' successfully Deleted')
        return redirect(url_for('showCatalog'))

    return render_template('deleteItem.html', category=category_name)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Get file from folder to display on page"""
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.errorhandler(404)
def page_not_found(e):
    """ Load Custom 404 Page """
    return render_template('404.html', error=e), 404


def checkCategory(category):
    """ Prevents fake category url name """
    q = session.query(Category).filter(Category.name == category).count()
    return q != 0


def unquieName(name, itemId=None):
    """ Gives a new image file a unique  file name"""
    if itemId:
        title = name.split('.', 1)[0]
        ending = name.split('.', 1)[-1]
        title += "_item_id_%s." % itemId
        newfilename = title + ending
        return newfilename
    else:
        title = name.split('.', 1)[0]
        ending = name.split('.', 1)[-1]
        randonNum = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
        title += "_new_" + randonNum + '.' + ending
        return title


def allowed_file(filename):
    """Make sure that user i uploading allowed file type"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def userLoggedIn():
    """Check it user is logged on"""
    if 'email' in login_session:
        return True
    else:
        return False


def userAdmin():
    """Check if user is an administrator"""
    if 'admin' in login_session:
        return login_session['admin']
    else:
        return False


def matchUser(post_user):
    """Make user match creator of item before they can edit or delete"""
    if userLoggedIn():
        signinUser = login_session['email']
        if signinUser == post_user:
            return True
    return False


app.jinja_env.globals['userLoggedIn'] = userLoggedIn
app.jinja_env.globals['userAdmin'] = userAdmin
app.jinja_env.globals['matchUser'] = matchUser

if __name__ == '__main__':
    app.debug = True
    app.run()
