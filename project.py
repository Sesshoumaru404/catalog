__author__ = 'sesshoumaru404@outlook.com (Paul)'

from flask import Flask, render_template, request, redirect,jsonify, url_for, flash, send_from_directory, make_response
from flask import session as login_session
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from flask_wtf.csrf import CsrfProtect
from sqlalchemy import create_engine, asc, text, inspect
from sqlalchemy.orm import sessionmaker
from catalog import Category, Base, Item
from sqlalchemy.sql import func
import os, json
import random, string, httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests


UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Project 3 Catalog App"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                         for x in xrange(32))
CsrfProtect(app)
#Connect to Database and create database session
engine = create_engine('sqlite:///categoryproject.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog/JSON')
def catalogJSON():
    catalogs = session.query(Category).all()
    return jsonify(restaurants=[r.column_descriptions for r in catalogs])

@app.route('/items/ATOM')
def catalogATOM():
    items = session.query(Item).all()
    feed = AtomFeed('Items', feed_url=request.url, url=request.url_root)

    for c in items:
        feed.add(c.name,
                 id= url_for('showItem'),
                 updated=c.create_At)
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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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

    login_session['user'] = data

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
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['user']

        flash('Successfully Logout.')
        return redirect(url_for('showCatalog'))
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


#Show all restaurants
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    subq = session.query(Item.category_id, func.count('*').label('item_count')).\
        group_by(Item.category_id).subquery()
    catalogCounts = session.query(Category.id, Category.name, subq.c.item_count).\
        outerjoin(subq, Category.id == subq.c.category_id).order_by(Category.name.asc())
    tencat = session.query(Item.id, Item.name, Item.image, Item.price, Category.name.label('cat_name')).\
        outerjoin(Category, Category.id == Item.category_id).order_by(Item.create_At.desc())
    tenLastest = session.query(Item).order_by(Item.create_At.desc())
    # Pagination(tenLastest,)
    userLoggedIn()
    return render_template('index.html', catalogs=catalogCounts, lastest=tencat)

@app.route('/catalog/<category_name>/<int:item_id>')
def showItem(category_name, item_id):
    if checkCategory(category_name):
        item = session.query(Item, Category.name.label('cat_name')).\
            outerjoin(Category, Category.id == Item.category_id).\
            filter(Item.id == item_id, Category.name == category_name).one()
        return render_template('show.html', item = item)
    else:
        return page_not_found("404: Not Found")

@app.route('/catalog/<category_name>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_id):
    categories =  session.query(Category.name).all()
    if checkCategory(category_name):
        if request.method == 'POST':
            editedItem = session.query(Item).filter_by(id=item_id).one()
            image = request.files['image']
            imagepath = None
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
                    return redirect(url_for('editItem', category_name = category_name, item_id = item_id))
            for attr in request.form:
                if request.form[attr]:
                    if attr == 'image':
                        pass
                    setattr(editedItem, attr, request.form[attr])
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showItem', category_name = category_name, item_id= item_id))
        item = session.query(Item.id, Item.name, Item.price, Item.description,
                             Item.create_At, Category.name.label('cat_name')).\
            outerjoin(Category, Category.id == Item.category_id).\
            filter(Item.id == item_id, Category.name == category_name).one()
        return render_template('edit.html', item = item, categories = categories )
    else:
        return page_not_found("404: Not Found")


@app.route('/catalog/<category_name>/items')
def categoryItems(category_name):
    if checkCategory(category_name):
        subq = session.query(Item.category_id, func.count('*').\
                             label('item_count')).\
                             group_by(Item.category_id).subquery()
        catalogCounts = session.query(Category.id, Category.name, subq.c.item_count).\
            outerjoin(subq, Category.id == subq.c.category_id).order_by(Category.name.asc())
        categoryItems = session.query(Item.id, Item.name, Item.price, Category.name.label('cat_name')).\
            outerjoin(Category, Category.id == Item.category_id).filter(Category.name == category_name)
        tenLastest = session.query(Item).order_by(Item.create_At.desc())
        return render_template('index.html', catalogs=catalogCounts, lastest=categoryItems, title=category_name)
    else:
        return page_not_found("404: Not Found")

# Delete a menu item
@app.route('/catalog/<category_name>/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(category_name, item_id):
    # if 'username' not in login_session:
    #     return redirect('/login')
    item = session.query(Item.id, Item.name, Item.price, Item.description,
                         Item.create_At, Item.edited_At, Category.name.label('cat_name')).\
        outerjoin(Category, Category.id == Item.category_id).\
        filter(Item.id == item_id, Category.name == category_name).one()
    itemToDelete = session.query(Item).filter(Item.id == item_id).one()
    if request.method == 'POST':
        if itemToDelete.image:
            os.remove(itemToDelete.image)
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html', item=item)

@app.route('/catalog/create', methods=['GET', 'POST'])
def createItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
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
                       image=imagepath)
        session.add(newItem)
        session.commit()
        flash('Item Successfully created')
        return redirect(url_for('showCatalog'))
    return render_template('new.html', categories = categories, new=True)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error = e), 404

def checkCategory(category):
    #Prevent fake url
    q = session.query(Category).filter(Category.name == category).count()
    return q != 0

def unquieName(name, itemId=None):
    if itemId:
        title = name.split('.',1)[0]
        ending = name.split('.',1)[-1]
        title += "_item_id_%s." % itemId
        newfilename = title + ending
        return newfilename
    else:
        title = name.split('.',1)[0]
        ending = name.split('.',1)[-1]
        randonNum = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(12))
        title += "_new_" + randonNum + '.' + ending
        return title

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def userLoggedIn():
    if 'user' in login_session:
        print login_session['user']
    else:
        print "False"


if __name__ == '__main__':
    app.secret_key = "Paul"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
