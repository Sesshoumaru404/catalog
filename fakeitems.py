from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database, create_database
from sqlalchemy.orm import sessionmaker

from catalog import Category, Base, Item

# if database_exists('sqlite:///categoryproject.db'):
#     drop_database('sqlite:///categoryproject.db')
#     create_database('sqlite:///categoryproject.db')

engine = create_engine('sqlite:///categoryproject.db')


# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Soccer Category
category1 = Category(name="soccer")
session.add(category1)
session.commit()

item1 = Item(name="blue Ball", description="Soccer ball with blue color",
                 price="$7.50", category=category1)

session.add(item1)
session.commit()

item2 = Item(name="red Ball", description="Soccer ball with red color",
                 price="$7.50", category=category1)

session.add(item2)
session.commit()

item3 = Item(name="Orange Ball", description="Soccer ball with orange color",
                 price="$7.50", category=category1)
session.add(item3)
session.commit()

# Basketball Category
category2 = Category(name="basketball")
session.add(category2)
session.commit()

item4 = Item(name="Blue Ball", description="Basketball with blue color",
                 price="$7.50", category=category2)

session.add(item4)
session.commit()

item5 = Item(name="Red Ball", description="Basketball with red color",
                 price="$7.50", category=category2)

session.add(item5)
session.commit()

item6 = Item(name="Orange Ball", description="Basketball with orange color",
                 price="$7.50", category=category2)
session.add(item6)
session.commit()

item7 = Item(name="Purple Ball", description="Basketball with purple color",
                 price="$7.50", category=category2)
session.add(item7)
session.commit()

item8 = Item(name="Street Ball", description="Basketball with grey color",
                 price="$7.50", category=category2)
session.add(item7)
session.commit()



print "added menu items!"
