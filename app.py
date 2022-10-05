from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from email import message
from urllib import request
from flask import Flask, render_template
from flask import Flask, redirect, url_for, render_template, request
import requests
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)

# session details
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
sess = Session()


@app.route('/')
def home():
    return render_template('index.html')

# login for the admin
@app.route('/admin_login', methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template('adminlogin.html')
    else:
        admin_email = "gecaadmin@gmail.com"
        admin_password = "admin123"

        # take the entered email and password by the user
        email = request.form["email"]
        password = request.form["password"]

        # check if the entered email and password are same as the declared one
        if(admin_email == email and admin_password == password):
            # if they are correct redirect them to the orders page
            return render_template('orders.html')
        else:
            message = "Email or password that you have entered is incorrect."
            return render_template('adminlogin.html', message=message)


#login for the user
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    else:
        # take the entered email and password by the user
        user_email = request.form["email"]
        user_password = request.form["password"]

        # check if the user exists in the database
        user = db.collection('users').where(
            "email", "==", f"{user_email}").stream()

        # retrive the password
        global password
        flag = 0
        for doc in user:
            u = doc.to_dict()
            flag = 1
            password = u["password"]

        # if no such user exists, show the appropriate message
        if flag == 0:
            message = "No such user exists. Please click on Sign-up to register"
            return render_template('login.html', message=message)

        # check if the password is matching with the entered password
        if(password == user_password):
            # password is correct
            # this shows user exists, direct them to the food-menu page
            #and add the curent user to the session
            session['current_user'] = user_email
            return redirect(url_for('display_menu'))
            
            
        else:
            #password is incorrect
            message = "Your password is incorrect. Please try again"
            return render_template('login.html', message=message)


@app.route('/sign-up', methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template('signup.html')
    else:
        # take the name, email and password
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # check if the mail already exists
        user_ref = db.collection('users').where(
            "email", "==", f"{email}").get()
        if user_ref != []:
            message = "User already exists. Please use a different Email"
            return render_template('signup.html', message=message)

        db.collection('users').add({
            'name': name,
            'email': email,
            'password': password
        })

        # display the message of successful account creation
        message = "User created successfully. Please now login with your username and password"

        return render_template('/signup.html', message=message)

# for admin only
# adding new items in the menu
@app.route('/admin/add_items', methods=["GET", "POST"])
def addItems():
    if request.method == "GET":
        return render_template("addItems.html")
    else:
        item_name = request.form.get("itemname").lower()
        item_image_link = request.form.get("imgurl")
        item_price = request.form.get("price")

        flag = 0

        docs = db.collection('Food_Items').get()
        for doc in docs:
            print(doc.to_dict())
            if doc.to_dict()['item_name'] == item_name:
                flag = 1
                break
            else:
                continue

        if flag == 0:
            data = {'item_name': item_name,
                    'item_img_link': item_image_link, 'item_price': item_price}
            db.collection('Food_Items').add(data)
            message = "Food Item Added successfully!"
            return render_template("addItems.html", message=message)
        else:
            message = "Food Item already exists!"
            return render_template("addItems.html", message=message)

# for admin only
# editing existing items in the menu
@app.route('/admin/edit_items', methods=["GET", "POST"])
def editItems():
    if request.method == "GET":
        return render_template("editItems.html")
    else:
        item_name = request.form.get("itemname").lower()
        item_image_link = request.form.get("imgurl")
        item_price = request.form.get("price")

        flag = 0
        docs = db.collection('Food_Items').get()
        for doc in docs:
            print(doc.to_dict())
            if doc.to_dict()['item_name'] == item_name:
                key = doc.id
                flag = 1
                break
            else:
                continue

        if flag == 0:
            message = "Specified item does not exist!, Add it to the database!"
            return render_template("editItems.html", message=message)
        else:
            updated_dict = {"item_img_link": item_image_link,
                            "item_price": item_price}
            db.collection('Food_Items').document(key).update(updated_dict)

            message = "Item updated successfully!"
            return render_template("editItems.html", message=message)

# displaying entire menu to the user by fetching food items from the database
@app.route('/menu-items', methods=["GET", "POST"])
def display_menu():
    global key
    global data_to_display
    if  request.method == "GET":
        docs = db.collection('Food_Items').get()
        data_to_display = []

        for doc in docs:
            data = doc.to_dict()
            #print(data)
            key = doc.id
            #appending data to display on the menu page
            d = [data.get('item_name'), data.get('item_img_link'), data.get('item_price'), key]
            data_to_display.append(d)

        return render_template("menu.html", data=data_to_display)
    else:
        
        #set the session user here
        # take the username from the login page (use session to retrive the username)
        user = session.get('current_user', None)

        #getting product id, name and quantity
        quantity = request.form.get('quantity')
        item_id = request.form.get('item_id')

        #check if quantity is null, show the error
        if(quantity==""):
            message = "Please select the quantity of the item."
            count = int(request.form.get('item_counter'))
            return render_template('menu.html', data=data_to_display, message = message, c = count)
        
        res = db.collection('Food_Items').document(item_id).get()
        dict = res.to_dict()
        
        name = dict['item_name']
        
        #getting user information from the 
        docs = (db.collection('users').where('email', '==', user).get())
        for doc in docs:
            key = doc.id
            
        #setting the item name and quatity into 'Buffer' collection
        data = {'item_name' : name, 'item_quantity' : quantity}
        db.collection('users').document(key).collection('Buffer').add(data)
       
        return render_template('menu.html', data=data_to_display, name = name)
       
if __name__ == '__main__':
    app.run(debug=True)
    sess.init_app(app)
