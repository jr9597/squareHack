from flask import Flask, request, render_template, jsonify
from square.client import Client
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import os
import json

environment = os.getenv('SQ_ENVIRONMENT')

client = Client(
    square_version='2021-06-16',
    access_token='AccessToken',
    environment='sandbox',  # for production -> sandbox
    custom_url='connect.squareupsandbox.com')  # for production -> connect.squareup.com

load_dotenv()  # take environment variables from .env.
# obtain_token = client.o_auth.obtain_token
# merchants_api = client.merchants


app = Flask(__name__)

# Your application's ID and secret, available from your application dashboard.
application_id = os.getenv('SQ_APPLICATION_ID')
application_secret = os.getenv('SQ_APPLICATION_SECRET')
base_url = "https://connect.squareup.com" if environment == "production" else "https://connect.squareupsandbox.com"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sellerinfo.db'
db = SQLAlchemy(app)

sellersAndLocations = db.Table('sellersAndLocations',
                               db.Column('seller_id', db.String(), db.ForeignKey('sellers.merchant_id')),
                               db.Column('location_id', db.String(), db.ForeignKey('locations.location_id'))
                               )

class Seller(db.Model):
    __tablename__ = 'sellers'
    merchant_id = db.Column(db.String(), primary_key=True)
    name = db.Column(db.String(), nullable=False)
    access_token = db.Column(db.String())
    refresh_token = db.Column(db.String(), nullable=False)
    locations = db.relationship("Location",
                                secondary=sellersAndLocations)


class Location(db.Model):
    __tablename__ = 'locations'
    location_id = db.Column(db.String(), primary_key=True)
    address_line_one = db.Column(db.String())
    state = db.Column(db.String())
    country = db.Column(db.String())
    city = db.Column(db.String())
    postal_code = db.Column(db.Integer)


@app.route('/', methods =['POST', 'GET'])
def home():

  if request.method == 'POST':
    sellerLocationIDs = request.form['content']

    sellerID = ""
    locationID = ""
    counter = 0
    for letter in sellerLocationIDs:
      if letter == ',':
        sellerID += sellerLocationIDs[0:counter]
        locationID += sellerLocationIDs[counter + 1:len(sellerLocationIDs)]
        break
      counter += 1

    currentSeller = Seller.query.get(sellerID)
    currentLocation = Location.query.get(locationID)

    currentAccessToken = currentSeller.access_token
    tempClient = Client(
      square_version='2021-06-16',
      access_token= currentAccessToken,
      environment='sandbox',  # for production -> sandbox
      custom_url='connect.squareupsandbox.com')
    orders_api = tempClient.orders

    body = {}
    body['location_ids'] = [locationID] #"LBG22PC6J5XKG"
    searchOrdersData = json.loads(orders_api.search_orders(body).text)
    itemDict = {}
    if searchOrdersData == {}:
      pass
    else:
      for order in searchOrdersData['orders']:
        for i in range(len(order['line_items'])):
          itemName = order['line_items'][i]['name']
          itemQuantity = int(order['line_items'][i]['quantity'])
          if itemDict.get(itemName) == None:
            itemDict[itemName] = itemQuantity
          else:
            itemDict[itemName] = itemDict[itemName] + itemQuantity
    
    sortedOrders = sorted(itemDict.items(), key=lambda x: x[1], reverse=True)

    sellers = Seller.query.all()
    return render_template('search.html', sellers = sellers, sortedOrders = sortedOrders, sellerName = currentSeller.name, locationName = currentLocation)

  sellers = Seller.query.all()

  return render_template('home.html', sellers = sellers)




@app.route('/authorization', methods=['GET'])
def authorize():
    url = "{0}/oauth2/authorize?client_id={1}".format(base_url, application_id)
    content = """
  <div class='text-justify'>
    <a class='btn'
     href='{}'>
       <strong>Authorize</strong>
    </a>
  </div>""".format(url)
    return render_template("authorize.html", content=content)



@app.route('/search', methods=['GET', 'POST'])
def search():
  if request.method == 'POST':
    sellerLocationIDs = request.form['content']
    sellerID = ""
    locationID = ""
    counter = 0
    for letter in sellerLocationIDs:
      if letter == ',':
        sellerID += sellerLocationIDs[0:counter]
        locationID += sellerLocationIDs[counter + 1:len(sellerLocationIDs)]
        break
      counter += 1

    currentSeller = Seller.query.get(sellerID)
    currentLocation = Location.query.get(locationID)

    currentAccessToken = currentSeller.access_token
    tempClient = Client(
      square_version='2021-06-16',
      access_token= currentAccessToken,
      environment='sandbox',  # for production -> sandbox
      custom_url='connect.squareupsandbox.com')
    orders_api = tempClient.orders
    body = {}
    body['location_ids'] = [locationID] #"LBG22PC6J5XKG"
    searchOrdersData = json.loads(orders_api.search_orders(body).text)

    itemDict = {}
    if searchOrdersData != None:
      for order in searchOrdersData['orders']:
        for i in range(len(order['line_items'])):
          itemName = order['line_items'][i]['name']
          itemQuantity = int(order['line_items'][i]['quantity'])
          if itemDict.get(itemName) == None:
            itemDict[itemName] = itemQuantity
          else:
            itemDict[itemName] = itemDict[itemName] + itemQuantity
    
    sortedOrders = sorted(itemDict.items(), key=lambda x: x[1], reverse=True)
    sellers = Seller.query.all()
    return render_template('search.html', sellers = sellers, sortedOrders = sortedOrders, sellerName = currentSeller.name, locationName = currentLocation)


  


# Serves requsts from Square to your application's redirect URL
# Note that you need to set your application's Redirect URL to
# http://localhost:8080/callback from your application dashboard
@app.route('/callback', methods=['GET'])
def callback():
    # Extract the returned authorization code from the URL
    authorization_code = request.args.get('code')



    if authorization_code:

        # Provide the code in a request to the Obtain Token endpoint
        body = {}
        body['client_id'] = application_id
        body['client_secret'] = application_secret
        body['code'] = authorization_code
        body['grant_type'] = 'authorization_code'
        body['scopes']=['ORDERS_READ']

        o_auth_api = client.o_auth
        response = o_auth_api.obtain_token(body)

        # dictionary version of response
        res = json.loads(response.text)

        if response.body:

            # Here, instead of printing the access token, your application server should store it securely
            # and use it in subsequent requests to the Connect API on behalf of the merchant.
            content = """
      <div class='wrapper'>
        <div class='messages'>
          <h1>Authorization Succeeded</h1>
            <div style='color:rgba(204, 0, 35, 1)'><strong>Caution:</strong> NEVER store or share OAuth access tokens or refresh tokens in clear text.
                Use a strong encryption standard such as AES to encrypt OAuth tokens. Ensure the production encryption key is not
                accessible to anyone who does not need it.
            </div>
            <br/>
            <div><strong>OAuth access token:</strong> {} </div>
            <div><strong>OAuth access token expires at:</strong> {} </div>
            <div><strong>OAuth refresh token:</strong> {} </div>
            <div><strong>Merchant Id:</strong> {} </div>
            <div><p>You can use this OAuth access token to call Create Payment and other APIs that were authorized by this seller.</p>
            <p>Try it out with <a href='https://developer.squareup.com/explorer/square/payments-api/create-payment' target='_blank'>API Explorer</a>.</p>
          </div>
        </div>
      </div>
      """.format(response.body['access_token'], response.body['expires_at'], response.body['refresh_token'],
                 response.body['merchant_id'])

            # client.access_token = response.body['access_token']
            tempClient = Client(
                square_version='2021-06-16',
                access_token=response.body['access_token'],
                environment='sandbox',  # for production -> sandbox
                custom_url='connect.squareupsandbox.com')

            merchants_api = tempClient.merchants
            merchantData = merchants_api.retrieve_merchant(response.body['merchant_id'])
            merchantName = merchantData.body['merchant']['business_name']

            locations_api = tempClient.locations
            locationListData = json.loads(locations_api.list_locations().text)
            sellerToAdd = Seller(access_token='EAAAEM5vhPeIEWE9b0N_jTSuFZXSTFZ5j2fWlflJtkjJCSTWpIFFaxRhQMBPNB43', merchant_id=res['merchant_id'],
                                 refresh_token=res['refresh_token'], name=merchantName)
            for locationListItem in locationListData['locations']:
                locationToAdd = Location(location_id=(locationListItem['id']),
                                         address_line_one=locationListItem['address']['address_line_1'],
                                         city=locationListItem['address']['locality'],
                                         state=locationListItem['address']['administrative_district_level_1'],
                                         postal_code=locationListItem['address']['postal_code'])
                sellerToAdd.locations.append(locationToAdd)
            db.session.add(sellerToAdd)
            db.session.commit()

            return render_template("authorize.html", content=content)
        # The response from the Obtain Token endpoint did not include an access token. Something went wrong.
        else:
            content = """
      <link type='text/css' rel='stylesheet' href='static/style.css'>
      <meta name='viewport' content='width=device-width'>
      <div class='wrapper'>
        <div class='messages'>
          <h1>Code exchange failed</h1>
        </div>
      </div>"""
            return render_template("authorize.html", content=content)

    # The request to the Redirect URL did not include an authorization code. Something went wrong.
    else:
        content = """
    <link type='text/css' rel='stylesheet' href='static/style.css'>
    <meta name='viewport' content='width=device-width'>
    <div class='wrapper'>
      <div class='messages'>
        <h1>Authorization failed</h1>
      </div>
    </div>"""
        return render_template("authorize.html", content=content)

if __name__ == "__main__":
    app.run(debug=True)