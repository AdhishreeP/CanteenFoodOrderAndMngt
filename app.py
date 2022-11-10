from flask import Flask, render_template, redirect, request, flash, session
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
        
        session['current_name'] = name
        session['current_user'] = email
        session['current_pass'] = password
        
        # check if the mail already exists
        user_ref = db.collection('users').where(
            "email", "==", f"{email}").get()
        if user_ref != []:
            message = "User already exists. Please use a different Email"
            return render_template('signup.html', message=message)

        return redirect(url_for('optforsignin', name = name, email = email, password = password))
       

@app.route('/otp-to-create-account', methods=["GET", "POST"])
def optforsignin():
    global otp
    if request.method == "GET":
        #generate the otp and send mail
        from multiprocessing import context
        import random
        import ssl
        import smtplib
        from email.message import EmailMessage

        email_sender = "canteenfoodordering@gmail.com"
        email_pass = "vcelxbvzlwarrhnk"

        user = session.get('current_user', None)
        email_receiver = user

        subject = "OTP for Sign-in"

        otp = random.randint(0,999999)

        body = f"""
        Your OTP for creating an account is: {otp}.
        Please don't share it with anyone.
        """

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com',465, context=context) as smtp:
            smtp.login(email_sender, email_pass)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        return render_template('otpforsignin.html')
    else:
        #check the otp is correct or not
        user_otp = request.form["otp"]
        
        email = session.get('current_user', None)
        name = session.get('current_name', None)
        password = session.get('current_pass', None)

        if otp == int(user_otp):
            db.collection('users').add({
            'name': name,
            'email': email,
            'password': password
        })
            # display the message of successful account creation
            message = "User created successfully. Please now login with your username and password."
            return render_template('otpforsignin.html', message = message)  
        else:
            message = "Your OTP is incorrrect."
            return render_template('otpforsignin.html', message = message)   
    
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


#order summary of the user
@app.route('/order_summary', methods=["GET", "POST"])
def order_summary():
    # set the session user here
    user = session.get('current_user', None)

    data_to_display = []
    grand_total = 0
    name = ""
    # getting user information
    docsusers = (db.collection('users').where('email', '==', user).get())
    for docs in docsusers:
        key = docs.id
        username = docs.to_dict()["name"]

    # appending data to display on the order summary page
    docsbuffer = db.collection('users').document(key).collection('Buffer').get()
    if docsbuffer == []:
        print("User didn't select anything")
        flash("Please select atleast one item.")
        return redirect(url_for('display_menu'))
    for doc in docsbuffer:
        print(doc)
        keybuffer = doc.id
        data = doc.to_dict()
        d = [keybuffer, data.get('item_name'), data.get('item_quantity')]
        name = data.get('item_name')
        docsfood = db.collection('Food_Items').where('item_name', '==', name).get()
        for df in docsfood:
            dict = df.to_dict()
            price = dict.get('item_price')
            d.append(price)
            break

        # Caculating total price for each item
        total = int(d[2]) * int(d[3])
        d.append(total)

        # calculating the total amount of all items
        grand_total = grand_total + total
        data_to_display.append(d)

    if request.method == "GET":
        session['total'] = grand_total
        return render_template("ordersummary.html", data=data_to_display, grand_total=grand_total, user=username)
    
    if request.method == "POST":
        remove_item_id = request.form.get('remove_item_id')
        print(remove_item_id)
        db.collection('users').document(key).collection('Buffer').document(remove_item_id).delete()

        data_to_display = []
        grand_total = 0

        # getting user information
        docsusers = (db.collection('users').where('email', '==', user).get())
        for docs in docsusers:
            key = docs.id
            username = docs.to_dict()["name"]

        # appending data to display on the order summary page
        docsbuffer = db.collection('users').document(key).collection('Buffer').get()
        if docsbuffer == []:
            print("User didn't select anything")
            flash("The order got empty..! Please select alteast one item.")
            return redirect(url_for('display_menu'))
        for doc in docsbuffer:
            print(doc)
            keybuffer = doc.id
            data = doc.to_dict()
            d = [keybuffer, data.get('item_name'), data.get('item_quantity')]
            name = data.get('item_name')
            docsfood = db.collection('Food_Items').where('item_name', '==', name).get()
            for df in docsfood:
                dict = df.to_dict()
                price = dict.get('item_price')
                d.append(price)
                break

            # Caculating total price for each item
            total = int(d[2]) * int(d[3])
            d.append(total)

            # calculating the total amount of all items
            grand_total = grand_total + total
            data_to_display.append(d)

        session['total'] = grand_total
        print("In post request: ", grand_total)
        return render_template("ordersummary.html", data=data_to_display, grand_total=grand_total, user=username)


global ls
ls = []
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

        return render_template("menu.html", data=data_to_display, ls = ls)
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
            return render_template('menu.html', data=data_to_display, message = message, c = count, ls = ls)
        
        res = db.collection('Food_Items').document(item_id).get()
        dict = res.to_dict()
        
        name = dict['item_name']
        
        #getting user information from the session
        docs = (db.collection('users').where('email', '==', user).get())
        for doc in docs:
            key = doc.id
           
        #setting the item name and quatity into 'Buffer' collection
        data = {'item_name' : name, 'item_quantity' : quantity}
        db.collection('users').document(key).collection('Buffer').add(data)
        ls.append(name)
        return render_template('menu.html', data=data_to_display, ls = ls)


#forgetting password
@app.route('/forgot-password', methods=["GET", "POST"])
def forgot_pass():

    if  request.method == "GET":
        return render_template('forgotpass.html')
    else:
        #get the email
        user_email = request.form["email"]
        session['current_user'] = user_email
        #check if it is available in the users
        user_ref = db.collection('users').where(
            "email", "==", f"{user_email}").get()

        #if it is, then redirect the user to the otp page
        if user_ref != []:
            return redirect(url_for('otp'))      
        
        #else show them an error that the mail doesn't exist
        else:
            message = "This email doesn't exist. Please create a new account."
            return render_template('forgotpass.html', message = message)

#send otp and then reset the password
@app.route('/otp', methods=["GET", "POST"])
def otp():
    global otp
    if  request.method == "GET":
        
        #generate the otp and send mail
        from multiprocessing import context
        import random
        import ssl
        import smtplib
        from email.message import EmailMessage

        email_sender = "canteenfoodordering@gmail.com"
        email_pass = "vcelxbvzlwarrhnk"

        user = session.get('current_user', None)
        email_receiver = user

        subject = "OTP for Resetting the Password"

        otp = random.randint(0,999999)

        body = f"""
        Your OTP for reseting the password is: {otp}.
        Please don't share it with anyone.
        """

        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com',465, context=context) as smtp:
            smtp.login(email_sender, email_pass)
            smtp.sendmail(email_sender, email_receiver, em.as_string())
        
        return render_template('otp.html')
    else:
        #check the otp is correct or not
        user_otp = request.form["otp"]
        if otp == int(user_otp):
            #redirect to a new page where password is reset
            return redirect(url_for('resetpass'))  
        else:
            message = "Your OTP is incorrrect."
            return render_template('otp.html', message = message)    

#resetting the password
@app.route('/reset-passsowrd', methods=["GET", "POST"])
def resetpass():
    if request.method == "GET":
        return render_template('resetpass.html')
    else:
        #take the new password
        newpass = request.form["password"]

        #update the password by retrieving the session of the user
        user = session.get('current_user', None)

        # get the document refernce for the particular user
        user_ref = db.collection('users').where("email", "==", f"{user}").get()

        # grab the document id
        global doc_id
        for user in user_ref:
            doc_id = user.id

        # update the password
        user = db.collection('users').document(f"{doc_id}")
        user.update({"password": newpass})

        # ender the page
        message = "Password updated successfully!!!"
        return render_template('resetpass.html', message=message)

global finalConfirm
finalConfirm = "notyet"
#order confirmation or cancellation
@app.route('/proceed', methods=['GET', 'POST'])
def test(): 
    grand_total = session.get('total', None)
    if request.method == "POST":
        if request.form["action"] == "yes":
            #retrieve the current user's session
            user = session.get('current_user', None)
            finalConfirm = "confirm"
            #retrieve the system date
            import datetime
            x = datetime.datetime.now()
            cur_date = x.strftime("%d-%m-%Y")

            #copy the order to the today's collection
            #add the order to user's profile as well
            docs = db.collection('users').where("email", "==", f"{user}").get()
            global id
            for doc in docs:
                id = doc.id

            items = db.collection('users').document(id).collection('Buffer').get()
            for item in items:
                i = item.to_dict()
                #for admin
                db.collection('Orders').document(f"{cur_date}").collection("current_orders").document(f"{user}").collection("order").add(i)
                #for user
                db.collection('users').document(id).collection('Orders').document(f"{cur_date}").collection("order").add(i)

            db.collection('Orders').document(f"{cur_date}").collection("current_orders").document(f"{user}").collection("order_total").add({"total" : grand_total })

            db.collection('users').document(id).collection('Orders').document(f"{cur_date}").collection("order_total").add({"total" : grand_total })

            #after copying delete the buffer
            for item in items:
                item_id = item.id
                db.collection('users').document(id).collection('Buffer').document(item_id).delete()
            
            #send the confirmation message
            message = f"Your order is confirmed. Pay {grand_total} Rs. at the counter"
            print("Order confirmed")

        elif request.form["action"] == "no":
            #retrieve the current user's session
            user = session.get('current_user', None)
            finalConfirm = "confirm"
            #delete the user's buffer
            docs = db.collection('users').where("email", "==", f"{user}").get()
            global id_user
            for doc in docs:
                id_user = doc.id_user

            items = db.collection('users').document(id_user).collection('Buffer').get()
            #deleting each item in the buffer
            for item in items:
                item_id = item.id
                db.collection('users').document(id_user).collection('Buffer').document(item_id).delete()

            #send the cancellation message
            message = "Your order is cancelled"
            print("Order Cancelled")
        print("at final confirmation: ", grand_total)
        return render_template('final.html', message = message, finalConfirm = finalConfirm )

    elif request.method =='GET':
        return render_template('final.html' )  

@app.route('/profile', methods=["GET"])
def profile():
    if request.method == "GET":
        #get the email from the session
        email = session.get('current_user', None)

        #retrieve name from the email
        docs = db.collection('users').where("email", "==", f"{email}").get()
        global id
        id = ""
        for doc in docs:
            id = doc.id
            name = doc.to_dict()["name"]

        allorders = db.collection('users').document(id).collection('Orders').get()
        print(allorders)
        for order in allorders:
            print(order.id)

        return render_template("profile.html", name = name, email = email)
if __name__ == '__main__':
    app.run(debug=True)
    sess.init_app(app)
