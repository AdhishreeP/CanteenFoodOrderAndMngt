import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

import datetime
x = datetime.datetime.now()
cur_date = x.strftime("%d-%m-%Y")

user = "samughodake1808@gmail.com"
docs = db.collection('users').where("email", "==", f"{user}").get()
global id
for doc in docs:
    id = doc.id

items = db.collection('users').document(id).collection('Buffer').get()
#deleting each item in the buffer
for item in items:
    i = item.to_dict()
    db.collection('Orders').document(f"{cur_date}").collection("current_orders").document(f"{user}").collection("order").add(i)

print("Order added to the admin")