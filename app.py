from imp import reload
from sqlalchemy.dialects.postgresql import UUID
from flask import Flask, jsonify, request, abort, send_file, session, Request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_session import Session
from flask_cors import CORS, cross_origin
from uuid import uuid4
from werkzeug.security import check_password_hash, generate_password_hash
import redis
from flask_bcrypt import Bcrypt
from decimal import Decimal
from sqlalchemy import ForeignKey
from flask_login import current_user, LoginManager, user_logged_in
import matplotlib.pyplot as plt
import requests
import matplotlib
import json
from apscheduler.schedulers.background import BackgroundScheduler
import os
from urllib.parse import urlparse


matplotlib.use('Agg')


app = Flask(__name__)

port = os.environ.get("REDIS_PORT")

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://ffbtctbuykfwze:f8f3ce9ef5eb1c755a1606cf333d51bd83ce373c836b208376aada71325d0c95@ec2-34-251-115-141.eu-west-1.compute.amazonaws.com:5432/dd7ha3irla8lna"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = "filesystem"
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
# port = os.environ.get("REDIS_PORT")
# app.config['SESSION_REDIS'] = redis.from_url(
#     "redis://:0z0dJeeK10hQfNLcu4Iv@flaskserv-4532.redis.a.osc-fr1.scalingo-dbs.com:40737")

app.config['SECRET_KEY'] = 'put_my_secret_key_here'
app.config['SESSION_COOKIE_NAME'] = "my_session"
app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = "None"


server_session = Session(app)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

cors_config = {
    "origins": ["*"]
}

CORS(app, supports_credentials=True, resources={
    r"/*": cors_config
})


def get_uuid():
    return uuid4().hex


class Cryptos(db.Model):
    __tablename__ = 'cryptos'
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   default=get_uuid)  # unique true
    name = db.Column(db.String(210), nullable=False)
    symbol = db.Column(db.String(210), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    date_of_buy = db.Column(db.DateTime(
        60), default=datetime.utcnow, nullable=False)
    crypto_id_CMC = db.Column(db.Integer, nullable=False)
    owner_user_id = db.Column(UUID(as_uuid=True), nullable=False)
    logo = db.Column(db.String(60), nullable=False)
    amountInvested = db.Column(db.Float, nullable=False)

    def __init__(self, name='', symbol='', quantity=0, price=0, owner_user_id=0, crypto_id_CMC=0, logo='', amountInvested=0):
        self.name = name
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.crypto_id_CMC = crypto_id_CMC
        self.owner_user_id = owner_user_id
        self.logo = logo
        self.amountInvested = amountInvested

    def __repr__(self):
        return f"Cryptos: {self.name, self.symbol ,self.quantity,self.price, self.crypto_id_CMC ,self.owner_user_id, self.logo, self.amountInvested}"


def format_event(event):
    return {
        "id": event.id,
        "date": event.date_of_buy,
        "name": event.name,
        "symbol": event.symbol,
        "quantity": event.quantity,
        "price": event.price,
        "crypto_id_CMC": event.crypto_id_CMC,
        "owner_user_id": event.owner_user_id,
        "logo": event.logo,
        "amount_invested": event.amountInvested
    }


@ app.route('/')
def index():
    return 'hey'

# cr??ation de l'evenement


@ cross_origin
@ app.route('/addcryptos', methods=['POST'])
def create_event():
    name = request.json['name']
    symbol = request.json['symbol']
    quantity = request.json['quantity']
    price = request.json['price']
    owner_user_id = request.json['owner_user_id']
    crypto_id_CMC = request.json['crypto_id_CMC']
    logo = request.json['logo']
    amountInvested = request.json['amountInvested']
    event = Cryptos(name, symbol, quantity, price,
                    owner_user_id, crypto_id_CMC, logo, amountInvested)
    db.session.add(event)
    db.session.commit()
    return format_event(event)


# classer par les id et les avoir dans une liste ?? faire ---------------------------mmm----------------------------------s


@ cross_origin
@ app.route('/addcryptos', methods=['GET'])
def get_events():
    events = Cryptos.query.order_by(Cryptos.id.asc()).all()
    event_list = []
    for event in events:
        event_list.append(format_event(event))
    return {'events': event_list}


# avoir le lien en rapport avec notre id de l'event
@ cross_origin
@ app.route('/addcryptos/<id>', methods=['GET'])
def get_event(id):
    event = Cryptos.query.filter_by(id=id).one()
    formatted_event = format_event(event)
    return {'event': formatted_event}


@cross_origin
@ app.route('/addcryptos/owner/<owner_user_id>', methods=['GET'])
def get_owner(owner_user_id):
    events = Cryptos.query.filter_by(owner_user_id=owner_user_id).all()
    event_list = []
    for event in events:
        event_list.append(format_event(event))
    # attention ilmanque quelque chose pour que ca renvoie
    return {'events': event_list}


@ cross_origin
@ app.route('/addcryptos/<id>', methods=['DELETE'])
def delete_event(id):
    event = Cryptos.query.filter_by(id=id).one()
    db.session.delete(event)
    db.session.commit()
    return f'La cryptomonnaie ?? bien ??t?? effac??'

# modifier un evenement


@cross_origin
@ app.route('/addcryptos/<id>', methods=['PUT'])
def update_event(id):
    event = Cryptos.query.filter_by(id=id)
    amountInvested = request.json['amountInvested']
    quantity = request.json['quantity']
    event.update(dict(amountInvested=amountInvested, quantity=quantity,
                      date_of_buy=datetime.utcnow()))
    db.session.commit()
    return {'event': format_event(event.one())}


# ------------------------------------------------------------Partie authentification ---------------------------------------------


class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True,
                   nullable=False, default=get_uuid)  # unique true
    email = db.Column(db.String(345), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    date_of_creation = db.Column(db.DateTime(
        60), default=datetime.utcnow, nullable=False)
    # user peut avoir plusieurs cryptomonnaies
    # crypto = db.relationship("Cryptos", backref='crypto_for_user')

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------------------Flask authentification --------------------------------------------------


@ cross_origin
@ app.route("/@me")
def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Non autoris??"}), 401

    user = Users.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email
    })


@ cross_origin
@ app.route('/register',  methods=["POST"])
def register_user():
    email = request.json["email"]
    password = request.json["password"]

    user_exists = Users.query.filter_by(email=email).first() is not None

    if user_exists:
        return jsonify({"error": "L'utilisateur existe d??ja"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = Users(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id

    return jsonify({
        "id": new_user.id,
        "email": new_user.email
    })


@ cross_origin
@ app.route('/login',  methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = Users.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Non autoris??"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401

    session["user_id"] = user.id

    return jsonify({
        "id": user.id,
        "email": user.email
    })


@ app.route("/logout", methods=["POST"])
def logout_user():
    session.pop("user_id")
    return "200"

# -----------------------------------Import API coin market cap-------------------------------


# --------------------------------------partie enregistrement une fois par jour de la valorisation du portemonnaie---------------------

@ cross_origin
@ app.route("/graphic")
def create_graph():

    user_id = session.get("user_id")
    user = Users.query.filter_by(id=user_id).first()

    plt.figure().clear()
    plt.figure()

    response_owner = requests.get(
        'https://www.azerbn.com/walletamount/owner/'+str(user_id)).json()

    datas = response_owner

    arr_of_amount = []
    arr_of_days = []

    for elements in datas:
        wallet = (elements['walletAmount'])
        arr_of_amount.append(wallet)
        arr_of_days.append(len(arr_of_amount))

    x = arr_of_days
    y = arr_of_amount

    ax = plt.gca()
    ax.set_facecolor('#100f0f')
    ax.spines['left'].set_color('#efefef')
    ax.figure.set_facecolor('#100f0f')
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_color('#efefef')
    ax.tick_params(axis='y', colors='#efefef')
    ax.xaxis.set_visible(False)

    plt.plot(x, y, color="#1fc36c")
    plt.axhline(y=0, color='#efefef')
    plt.ylabel('Pertes et gains', color='#efefef')
    plt.xlabel('Temps', color='#efefef')
    plt.savefig('graph.png')

    return send_file('graph.png', mimetype='image/png')

    #--------------------------------------------tache automatique----------------------------#


@app.route('/walletamount', methods=['POST'])
def post_user_wallet_infos():

    Usersdatas = requests.get('https://www.azerbn.com/addcryptos').json()

    infos = Usersdatas['events']

    array_of_id = []
    arr_of_amount_invested = []
    arr_of_price = []
    arr_of_crypto_id = []
    arr_of_current_amount = []
    arr_of_capital_by_user = []

    for elements in infos:

        users_id = elements['owner_user_id']
        amounts_invested = elements['amount_invested']
        crypto_id = elements['crypto_id_CMC']
        prices = elements['price']

        arr_of_price.append(prices)

        arr_of_amount_invested.append(amounts_invested)

        array_of_id.append(users_id)
        arr_of_user_id_once = list(set(array_of_id))

        arr_of_crypto_id.append(crypto_id)
        arr_crypto_id_once = list(set(arr_of_crypto_id))

# liste des user id un par un
    for i in arr_of_user_id_once:
        individual_user_id = i

        Users_datas = requests.get(
            'https://www.azerbn.com//addcryptos/owner/'+str(individual_user_id)).json()  # faire en sorte que users_id apparaire que 1 fois et que le prix des crypto est trier selon l'id


# initial price
        price_by_user = {}
        for data in Users_datas['events']:
            if data.get('owner_user_id') not in price_by_user:
                price_by_user[data.get('owner_user_id')] = [data.get('price')]
            else:
                price_by_user[data.get('owner_user_id')].append(
                    data.get('price'))

# quantity
        quantity_by_user = {}
        for datas in Users_datas['events']:
            if datas.get('owner_user_id') not in quantity_by_user:
                quantity_by_user[datas.get('owner_user_id')] = [
                    datas.get('quantity')]
            else:
                quantity_by_user[datas.get('owner_user_id')].append(
                    datas.get('quantity'))


# crypto id
        crypto_id_for_user = {}
        for datas in Users_datas['events']:
            if datas.get('owner_user_id') not in crypto_id_for_user:
                crypto_id_for_user[datas.get('owner_user_id')] = [
                    datas.get('crypto_id_CMC')]  # prend la donn??e
            else:  # ajoute dans un tableau
                crypto_id_for_user[datas.get('owner_user_id')].append(
                    datas.get('crypto_id_CMC'))

# montant investi
        amount_invested_by_user = {}
        for datas in Users_datas['events']:
            if datas.get('owner_user_id') not in amount_invested_by_user:
                amount_invested_by_user[datas.get('owner_user_id')] = [
                    datas.get('amount_invested')]  # prend la donn??e
            else:  # ajoute dans un tableau
                amount_invested_by_user[datas.get('owner_user_id')].append(
                    datas.get('amount_invested'))

        arr_of_amount_by_user = amount_invested_by_user[individual_user_id]
# capital de d??part par utilisateur
        sum_of_investisment_by_user = sum(arr_of_amount_by_user)

# liste des id cryptos par utilisateur (string)
        id_of_crypto_request = ','.join(
            str(x) for x in crypto_id_for_user[individual_user_id])

        CMC_Datas = requests.get(
            'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?id='+str(id_of_crypto_request)+'&convert=EUR&CMC_PRO_API_KEY=f407b3dc-20ca-4ee5-8938-af560b89eb59').json()

# tableau des identifiant des cryptos par utilisateur
        arr_of_id_by_user = crypto_id_for_user[individual_user_id]

        arr_of_price_by_user = []

        for x in arr_of_id_by_user:
            current_price = CMC_Datas['data'][str(x)]['quote']['EUR']['price']
            arr_of_price_by_user.append(current_price)

        amount_invested_x_current_price = [x*y for x, y in zip(arr_of_amount_by_user,
                                                               arr_of_price_by_user)]

        actual_amount_arr = [x/y for x, y in zip(amount_invested_x_current_price,
                                                 price_by_user[individual_user_id])]

        actual_amount_result = sum(actual_amount_arr)

        amount = actual_amount_result - sum_of_investisment_by_user

        arr_of_current_amount.append(amount)

        arr_of_capital_by_user.append(sum_of_investisment_by_user)

        datas_to_post_every_1_day = {"owner_id": i, 'walletAmount': amount,
                                     'initial amount invested':  sum_of_investisment_by_user}

        lala = (open('filed.json', 'r'))

    # with open('filed.json', 'w') as file:
    #     json.dump([{'owner_id': id, 'walletAmount': current_amount, 'initial amount invested': capital} for id, current_amount, capital in zip(
    #         arr_of_user_id_once, arr_of_current_amount, arr_of_capital_by_user)], file)

        jsonfile = open('filed.json')
        data = json.load(jsonfile)
        data.append(datas_to_post_every_1_day)
        print(datas_to_post_every_1_day)

        with open("filed.json", "w") as file:
            json.dump(data, file)

    return lala.read()


sched = BackgroundScheduler(daemon=True)
sched.add_job(post_user_wallet_infos, 'interval',
              minutes=30)
sched.start()


@cross_origin
@app.route('/walletamount', methods=['GET'])
def get_user_wallet_infos():
    lala = (open('filed.json', 'r'))
    return lala.read()


@cross_origin
@ app.route('/walletamount/owner/<owner_user_id>', methods=['GET'])
def filter_owner_wallet_amount(owner_user_id):
    # infos = requests.get('https://www.azerbn.com/walletamount').json()

    with open('filed.json') as file:
        data = json.load(file)
    # user = Users.query.filter_by(id=owner_user_id).first()
        output_dict = [x for x in data if x['owner_id'] == owner_user_id]
        output_json = json.dumps(output_dict)
        return output_json


@cross_origin
@ app.route('/cmclist', methods=['GET'])
def datas_CMC_list():
    datas = requests.get(
        'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?convert=EUR&CMC_PRO_API_KEY=f407b3dc-20ca-4ee5-8938-af560b89eb59').json()

    return jsonify(datas)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
