from flask import Flask, render_template, request, redirect,jsonify, url_for, flash, send_from_directory
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from flask_wtf.csrf import CsrfProtect
from sqlalchemy import create_engine, asc, text, inspect
from sqlalchemy.orm import sessionmaker
from catalog import Category, Base, Item
from sqlalchemy.sql import func
import os
import random
import string

UPLOAD_FOLDER = 'images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
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

@app.route('/login')
def showLogin():
    return render_template('login.html')

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


if __name__ == '__main__':
    app.secret_key = "Paul"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
