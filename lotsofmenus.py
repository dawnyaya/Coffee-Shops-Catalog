from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Coffee, Base, MenuItem, User

engine = create_engine('sqlite:///coffeeMenu.db')
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


# Create user Jenny
User1 = User(
  name="Jenny",
  email="dawnyayas@gmail.com",
)
session.add(User1)
session.commit()

# Add Coffee shops and its menus.

# Added Starbucks coffee shop.
coffee1 = Coffee(user_id=1, name="Starbucks")
session.add(coffee1)
session.commit()

# Added Freshly Brewed Coffee "Blonde Roast"
menuItem1 = MenuItem(
  user_id=1, 
  name="Blonde Roast", 
  description="""Lightly roasted coffee that's soft, mellow and flavorful.
  Easy-drinking on its own and delicious with milk, sugar or
  flavored with vanilla, caramel or hazelnut.""",
  price="$3.50", 
  category="Freshly Brewed Coffee",
  coffee=coffee1
)
session.add(menuItem1)
session.commit()

# Added Freshly Brewed Coffee "Caffe Misto"
menuItem2 = MenuItem(
  user_id=1,
  name="Caffe Misto",
  description="Freshly brewed coffee with steamed milk",
  price="$2.99",
  category="Freshly Brewed Coffee",
  coffee=coffee1
)
session.add(menuItem2)
session.commit()

# Added Iced Coffee "Iced Coffee with Milk"
menuItem3 = MenuItem(
  user_id=1,
  name="Iced Coffee with Milk",
  description="""Freshly brewed Starbucks Iced Coffee Blend with milk
  served chilled and lightly sweetened over ice""",
  price="$4.75",
  category="Iced Coffee",
  coffee=coffee1
)
session.add(menuItem3)
session.commit()

# Added Chocolate Beverages "Hot Chocolate"
menuItem4 = MenuItem(
  user_id=1,
  name="Hot Chocolate",
  description="""Steamed milk with vanilla- and mocha-flavored syrups.
  Topped with sweetened whipped cream and chocolate-flavored drizzle.""",
  price="$3.99",
  category="Chocolate Beverages",
  coffee=coffee1
)
session.add(menuItem4)
session.commit()

# Added Iced tea "Shaken Sweet Tea"
menuItem5 = MenuItem(
  user_id=1,
  name="Shaken Sweet Tea",
  description="""Delicious black tea with cane sugar""",
  price="$2.99",
  category="Iced tea",
  coffee=coffee1
)
session.add(menuItem5)
session.commit()

# Added Coffee shop Nature Brew.
coffee2 = Coffee(user_id=1, name="Nature Brew")
session.add(coffee2)
session.commit()

# Added Hot Beverages "Latte"
menuItem1 = MenuItem(
  user_id=1, 
  name="Latte",
  description="coffee-based drink made primarily from espresso and steamed milk",
  price="$3.95",
  category="Hot Beverages",
  coffee=coffee2
)
session.add(menuItem1)
session.commit()

# Added Hot Beverages "Espresso"
menuItem2 = MenuItem(
  user_id=1, 
  name="Espresso",
  description="A full-flavored, concentrated form of coffee that is served in shots",
  price="$2.50",
  category="Hot Beverages",
  coffee=coffee2
)
session.add(menuItem2)
session.commit()

# Added Cold Beverages "Iced Tea"
menuItem3 = MenuItem(
  user_id=1, 
  name="Iced Tea",
  description="Delicious green tea with cane sugar",
  price="$3.10",
  category="Cold Beverages",
  coffee=coffee2
)
session.add(menuItem3)
session.commit()

# Added Cold Beverages "Lemonade"
menuItem4 = MenuItem(
  user_id=1, 
  name="Lemonade",
  description="Iced honey Lemonade",
  price="$2.50",
  category="Cold Beverages",
  coffee=coffee2
)
session.add(menuItem4)
session.commit()
print "added menu items!"
