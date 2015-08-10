from flask import Flask, render_template, request, redirect,jsonify, url_for, flash
from sqlalchemy import create_engine, asc, text
from sqlalchemy.orm import sessionmaker
from catalog import Category, Base, Item
from sqlalchemy.sql import func

app = Flask(__name__)

#Connect to Database and create database session
engine = create_engine('sqlite:///categoryproject.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

#Show all restaurants
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    subq = session.query(Item.category_id, func.count('*').label('item_count')).\
        group_by(Item.category_id).subquery()
    catalogCounts = session.query(Category.id, Category.name, subq.c.item_count).\
        outerjoin(subq, Category.id == subq.c.category_id)
    tencat = session.query(Item.id, Item.name, Item.price, Category.name.label('cat_name')).\
        outerjoin(Category, Category.id == Item.category_id)
    tenLastest = session.query(Item).order_by(Item.create_At.desc())
    # Pagination(tenLastest,)
    print tencat
    return render_template('index.html', catalogs=catalogCounts, lastest=tencat)

@app.route('/catalog/<category_name>/<int:item_id>')
def showItem(category_name, item_id):
    if checkCategory(category_name):
        item = session.query(Item.id, Item.name, Item.price, Item.description,
                             Item.create_At, Item.edited_At, Category.name.label('cat_name')).\
            outerjoin(Category, Category.id == Item.category_id).\
            filter(Item.id == item_id, Category.name == category_name).one()
        return render_template('show.html', item = item)
    else:
        return page_not_found("404: Not Found")

@app.route('/catalog/<category_name>/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(category_name, item_id):
    if checkCategory(category_name):
        editedItem = session.query(Item).filter_by(id=item_id).one()
        if request.method == 'POST':
            for x in request.form:
                print editedItem
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['price']:
                editedItem.price = request.form['price']
            if request.form['category_id']:
                editedItem.category_id = request.form['category_id']
            session.add(editedItem)
            session.commit()
            flash('Item Successfully Edited')
            return redirect(url_for('showCatalog'))
        categories =  session.query(Category).all()
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
            outerjoin(subq, Category.id == subq.c.category_id)
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
        print itemToDelete
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html', item=item)

@app.route('/catalog/create', methods=['GET', 'POST'])
def createItem():
    categories =  session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       description=request.form['description'],
                       price=request.form['price'],
                       category_id=request.form['cat_id'])
        session.add(newItem)
        session.commit()
        flash('Item Successfully created')
        return redirect(url_for('showCatalog'))
    return render_template('new.html', categories = categories)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', error = e), 404

def checkCategory(category):
    #Prevent fake url
    q = session.query(Category).filter(Category.name == category).count()
    return q > 0




if __name__ == '__main__':
    app.secret_key = "Paul"
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
