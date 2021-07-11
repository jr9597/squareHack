# app = Flask(__name__)

# @app.route('/')
# def home():
#     return 'This is our humble homepage'

# if __name__ == "__main__":
#     app.run(debug=True)

    # This sample demonstrates a bare-bones implementation of the Square Connect OAuth flow:
#
# 1. A merchant clicks the authorization link served by the root path (http://localhost:8080/)
# 2. The merchant signs in to Square and submits the Permissions form. Note that if the merchant
#    is already signed in to Square, and if the merchant has already authorized your application,
#    the OAuth flow automatically proceeds to the next step without presenting the Permissions form.
# 3. Square sends a request to your application's Redirect URL
#    (which should be set to http://localhost:8080/callback on your application dashboard)
# 4. The server extracts the authorization code provided in Square's request and passes it
#    along to the Obtain Token endpoint.
# 5. The Obtain Token endpoint returns an access token your application can use in subsequent requests
#    to the Connect API.

from flask import Flask, request, render_template
from square.client import Client
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
import os;



environment = os.getenv('SQ_ENVIRONMENT')

client = Client(
    square_version='2021-06-16',
    access_token='AccessToken',
    environment = 'sandbox',
    custom_url = 'https://connect.squareup.com',)

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

class Seller(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name: db.Column(db.String(), nullable = False)
  accessToken: db.Column(db.String(), nullable = False)
  refreshToken: db.Column(db.String(), nullable = False)
  merchantID: db.Column(db.String(), nullable = False)
  locations: db.Column(db.String())
  def __repr__(self):
        return '<Seller %r>' % self.name



@app.route('/')
def home():
  sellers = Seller.query.all()
  print(sellers)
  return render_template('home.html', sellers = sellers)
  # task_content = request.args.get['content']
  # if task_content == "":
  #   return render_template("home.html")
  # else:
  #   try:
  #     # sellers = Seller.query.filter_by(name='content')
  #     seller = "hi"
  #     return render_template("search.html", sellers = seller )
  #   except:
  #     return render_template('home.html')
  




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


# @app.route('/search/<string:id>')
# def search(id):
#   seller_to_show = Seller.query

@app.route('/search')
def search():
  return render_template("search.html")


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

    o_auth_api = client.o_auth
    response = o_auth_api.obtain_token(body)

    if response.body:

      # Here, instead of printing the access token, your application server should store it securely
      # and use it in subsequent requests to the Connect API on behalf of the merchant.
      print (response.body)
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
      """.format(response.body['access_token'], response.body['expires_at'], response.body['refresh_token'], response.body['merchant_id'])
      
      client.access_token = response.body['access_token']
      merchants_api = client.merchants
      merchantAPICall = merchants_api.retrieve_merchant(response.body['merchant_id'])
      print(merchantAPICall.body)
      merchantName = merchantAPICall.body['business_name']
      sellerToAdd = Seller(accessToken = response.body['access_token'], merchantID = response.body['merchant_id'], refreshToken = response.body['refresh_token'], name = merchantName)
      
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
