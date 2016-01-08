from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Coffee, MenuItem, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
        open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Coffee Shop Menu Application"

# Connect to Database and create database session
engine = create_engine('sqlite:///coffeeMenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#  Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
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
    print "my access_token=" + access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Check 1: If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    # Check 2: Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check 3: Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    # Check if specific user already login.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['access_token'] = access_token
    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # Get user_id for user who successfully login.
    # Create user_id and store it in session variable if not have done yet.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    # Create output HTML
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


# DisConnect
@app.route('/gdisconnect')
def gdisconnect():
    # Get access token info and print on screen.
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    # If access_token is null return error message.
    if access_token is None:
        print 'Access Token is None'
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Send revoke request to google+
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']  # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    # Delete all session variables if revoke request is good.
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash('Successfully disconnected')
        return redirect(url_for('show_coffee_shops'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# User Helper Functions
def createUser(login_session):
    # For new users who have google account and use our app first.
    # We would like to store their information in database.
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    # Given user_id, return user object.
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    # Given user email, return user_id.
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# JSON APIs to view Coffee Shop Information.
@app.route('/coffee_shops/JSON')
def coffee_shop_JSON():
    coffee_shops = session.query(Coffee).all()
    return jsonify(coffee_shops=[r.serialize for r in coffee_shops])


# JSON API to view specific Coffee Shop menus
@app.route('/coffee_shops/<int:coffee_shop_id>/menu/JSON')
def menu_coffee_shop_JSON(coffee_shop_id):
    coffee_shop = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    items = session.query(MenuItem).filter_by(
        coffee_id=coffee_shop_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurants/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(
        id=menu_id).one()
    return jsonify(MenuItems=item.serialize)


# Show all coffee shops
@app.route('/')
@app.route('/coffee_shops/')
def show_coffee_shops():
    coffee_shops = session.query(Coffee).all()
    if 'username' not in login_session:
        return render_template(
            'public_coffee_shops.html', coffee_shops=coffee_shops)
    else:
        return render_template('coffee_shops.html', coffee_shops=coffee_shops)


# Create a new coffee shop
@app.route('/coffee_shops/new', methods=['GET', 'POST'])
def new_coffee_shop():
    # Login check first
    if 'username' not in login_session:
        return redirect('/login')
    # Create new coffee shop with user_id attribute
    if request.method == 'POST':
        new_coffee_shop = Coffee(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(new_coffee_shop)
        session.commit()
        flash('New Coffee Shop %s Successfully Created' % new_coffee_shop.name)
        return redirect(url_for('show_coffee_shops'))
    else:
        return render_template('new_coffee_shop.html')


# Delete a coffee shop
@app.route(
    '/coffee_shops/<int:coffee_shop_id>/delete', methods=['GET', 'POST']
    )
def delete_coffee_shop(coffee_shop_id):
    # Login check first
    if 'username' not in login_session:
        return redirect('/login')
    # Get specific coffee shop object
    delete_coffee_shop = session.query(Coffee).get(coffee_shop_id)
    # Check delete permission by diff user_id
    if delete_coffee_shop.user_id != login_session['user_id']:
        Error = ''
        Error += '<script>function myFunc()'
        Error += '{alert("You do not have permission to delete this Shop");}'
        Error += 'setTimeout(function() {'
        Error += 'window.location.href = "/coffee_shops";}, 2000);'
        Error += '</script><body onload="myFunc()">'
        return Error
    # Delete Coffee Shop
    if (request.method == 'POST'):
        session.delete(delete_coffee_shop)
        session.commit()
        flash('Coffee shop %s Successfully Deleted' % delete_coffee_shop.name)
        return redirect(url_for('show_coffee_shops'))
    else:
        return render_template(
            'delete_coffee_shop.html', delete_coffee_shop=delete_coffee_shop)


# Edit a coffee shop
@app.route('/coffee_shops/<int:coffee_shop_id>/edit/', methods=['GET', 'POST'])
def edit_coffee_shop(coffee_shop_id):
    # Login Check
    if 'username' not in login_session:
        return redirect('/login')
    # Get specific coffee shop object
    edit_coffee_shop = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    # Check edit permission by diff user_id
    if edit_coffee_shop.user_id != login_session['user_id']:
        Error = ''
        Error += '<script>function myFunc()'
        Error += '{alert("You do not have permission to edit this Shop");}'
        Error += 'setTimeout(function() {'
        Error += 'window.location.href = "/coffee_shops";}, 2000);'
        Error += '</script><body onload="myFunc()">'
        return Error
    # Edit Coffee Shop
    if request.method == 'POST':
        if request.form['name']:
            edit_coffee_shop.name = request.form['name']
            flash(
                'Coffee shop %s Successfully Edited ' % edit_coffee_shop.name
                )
            return redirect(url_for('show_coffee_shops'))
    else:
        return render_template(
            'edit_coffee_shop.html', edit_coffee_shop=edit_coffee_shop
            )


# Show coffee shop all menus
@app.route('/coffee_shops/<int:coffee_shop_id>/')
@app.route('/coffee_shops/<int:coffee_shop_id>/menu/')
def Menu_coffee_shop(coffee_shop_id):
    coffee_shop = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    items = session.query(MenuItem).filter_by(coffee_id=coffee_shop_id)
    categories = {}
    for item in items:
        if item.category not in categories.keys():
            categories[item.category] = 1
    print categories
    if ('username' not in login_session or
            coffee_shop.user_id != login_session['user_id']):
        return render_template(
            'public_menu.html', items=items,
            coffee_shop=coffee_shop, categories=categories
            )
    else:
        return render_template(
            'menu.html', coffee_shop=coffee_shop,
            items=items, categories=categories
            )


# Create a menu item for a coffee shop
@app.route('/coffee_shops/<int:coffee_shop_id>/new/', methods=['GET', 'POST'])
def newMenuItem(coffee_shop_id):
    # Login Check
    if 'username' not in login_session:
        return redirect('/login')
    # Get specific coffee shop
    coffee_shop = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    # Check create permission by diff user_id(restaurant)
    if login_session['user_id'] != coffee_shop.user_id:
        Error = ''
        Error += '<script>function myFunc()'
        Error += '''{alert("You do not have permission
        to create menu for this Shop");}'''
        Error += 'setTimeout(function() {'
        Error += 'window.location.href = "/coffee_shops";}, 2000);'
        Error += '</script><body onload="myFunc()">'
        return Error
    # Create one menu for this coffee shop
    if request.method == 'POST':
        newItem = MenuItem(
            name=request.form['name'],
            price=request.form['price'],
            description=request.form['description'],
            category=request.form['category'],
            coffee_id=coffee_shop_id,
            user_id=coffee_shop.user_id
            )
        session.add(newItem)
        session.commit()
        flash("New menu item %s created!" % newItem.name)
        return redirect(
            url_for('Menu_coffee_shop', coffee_shop_id=coffee_shop_id)
            )
    else:
        return render_template(
            'newmenuitem.html', coffee_shop_id=coffee_shop_id
            )


# Edit a menu item for a restaurant
@app.route(
    '/coffee_shops/<int:coffee_shop_id>/<int:menu_id>/edit/',
    methods=['GET', 'POST'])
def editMenuItem(coffee_shop_id, menu_id):
    # Login Check
    if 'username' not in login_session:
        return redirect('/login')
    # Get specific coffee shop and Menu Item
    coffee_shop = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    # Check edit permission by diff user_id
    if (login_session['user_id'] != coffee_shop.user_id or
            login_session['user_id'] != editedItem.user_id):
        Error = ''
        Error += '<script>function myFunc(){alert('
        Error += '"You do not have permission to edit menu for this Shop");}'
        Error += 'setTimeout(function() {'
        Error += 'window.location.href = "/coffee_shops";}, 2000);'
        Error += '</script><body onload="myFunc()">'
        return Error
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['category']:
            editedItem.category = request.form['category']
        session.add(editedItem)
        session.commit()
        flash("Menu item %s has been edited!" % editedItem.name)
        return redirect(
            url_for('Menu_coffee_shop', coffee_shop_id=coffee_shop_id)
            )
    else:
        return render_template(
            'editmenuitem.html', coffee_shop_id=coffee_shop_id,
            menu_id=menu_id, i=editedItem
            )


# Delete a menu item for a restaurant
@app.route(
    '/coffee_shops/<int:coffee_shop_id>/<int:menu_id>/delete/',
    methods=['GET', 'POST'])
def deleteMenuItem(coffee_shop_id, menu_id):
    # Login Check
    if 'username' not in login_session:
        return redirect('/login')
    # Get specific restaurant and Menu Item
    restaurant = session.query(Coffee).filter_by(id=coffee_shop_id).one()
    deletedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    # Check edit permission by diff user_id(restaurant)
    if (login_session['user_id'] != restaurant.user_id or
            login_session['user_id'] != deletedItem.user_id):
        Error = ''
        Error += '<script>function myFunc(){alert('
        Error += '"You do not have permission to edit menu for this Shop");}'
        Error += 'setTimeout(function() {'
        Error += 'window.location.href = "/coffee_shops";}, 2000);'
        Error += '</script><body onload="myFunc()">'
        return Error
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()
        flash("Menu item %s has been deleted!" % deletedItem.name)
        return redirect(
            url_for('Menu_coffee_shop', coffee_shop_id=coffee_shop_id)
            )
    else:
        return render_template(
            'deletemenuitem.html',
            coffee_shop_id=coffee_shop_id,
            menu_id=menu_id, i=deletedItem
            )


if __name__ == '__main__':
        app.secret_key = 'super_secret_key'
        app.debug = True
        app.run(host='0.0.0.0', port=5000)
