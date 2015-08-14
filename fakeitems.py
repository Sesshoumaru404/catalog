import random
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, drop_database, create_database
from sqlalchemy.orm import sessionmaker

from catalog import Category, Base, Item, User

# if database_exists('sqlite:///categoryproject.db'):
#     drop_database('sqlite:///categoryproject.db')
# else:
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

sports = {"soccer", "basketball", "tennis", "polo", "track",
        "swimming", "racing", "football", "baseball", "golf", "skydiving",
        "games", "chess"}

# user = User(name="test", email="sdfsdf@fdfd.vov")
# session.add(user)
# session.commit()


for sport in sports:
    category = Category(name=sport)
    session.add(category)
    session.commit()
    for i in range(random.randint(1,20)) :
        name = sport + ' item ' + str(i+1)
        item = Item(name=name,
                    description="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi cursus luctus dapibus. Aenean ut quam eu sapien malesuada porta ut non quam. Etiam cursus maximus eros eu pharetra. Fusce finibus turpis ipsum, quis vehicula libero molestie sed. Aenean cursus viverra nulla, vel venenatis dui vulputate in. Morbi et aliquet erat. Duis eget lacus quis lorem iaculis ornare ut quis dui. Vivamus euismod, sapien nec varius sodales, justo lacus mattis erat, non pellentesque arcu nulla ut neque. Aenean sagittis consectetur sem eu tristique. Donec consectetur turpis tincidunt risus euismod tincidunt. Sed lacus turpis, iaculis nec nulla eget, varius pretium magna. Aliquam vitae magna vitae elit eleifend suscipit eget eu arcu. Nunc dolor ex, bibendum id purus quis, tempus bibendum augue. Praesent consequat sapien risus, quis fermentum velit tincidunt imperdiet. Cras lacinia tempus libero, sed mollis ante tincidunt non.",
                    price=7.50,
                    category=category)
        session.add(item)
        session.commit()

print "added menu items!"
