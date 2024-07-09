#1. Project Setup
mkdir: ("ecommerce_app")
cd: ("ecommerce_app")
pip install(" Flask Flask-SQLAlchemy")

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    from app import routes, models
    return app

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

#2. Database Models
from datetime import datetime
from app import db

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    accounts = db.relationship('CustomerAccount', backref='customer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)

class CustomerAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    order_items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product')

#3. CRUD Endpoints for Customers and Customer Accounts
from flask import request, jsonify
from app import app, db
from app.models import Customer, CustomerAccount

@app.route('/customers', methods=['POST'])
def create_customer():
    data = request.get_json()
    new_customer = Customer(name=data['name'], email=data['email'], phone=data['phone'])
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': 'Customer created successfully'}), 201

@app.route('/customers/<int:id>', methods=['GET'])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return jsonify({'id': customer.id, 'name': customer.name, 'email': customer.email, 'phone': customer.phone})

@app.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    data = request.get_json()
    customer.name = data['name']
    customer.email = data['email']
    customer.phone = data['phone']
    db.session.commit()
    return jsonify({'message': 'Customer updated successfully'})

@app.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': 'Customer deleted successfully'})

@app.route('/customeraccounts', methods=['POST'])
def create_customer_account():
    data = request.get_json()
    customer = Customer.query.get_or_404(data['customer_id'])
    new_account = CustomerAccount(username=data['username'], password=data['password'], customer=customer)
    db.session.add(new_account)
    db.session.commit()
    return jsonify({'message': 'Customer account created successfully'}), 201

@app.route('/customeraccounts/<int:id>', methods=['GET'])
def get_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    return jsonify({'id': account.id, 'username': account.username, 'customer_id': account.customer_id})

@app.route('/customeraccounts/<int:id>', methods=['PUT'])
def update_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    data = request.get_json()
    account.username = data['username']
    account.password = data['password']
    db.session.commit()
    return jsonify({'message': 'Customer account updated successfully'})

@app.route('/customeraccounts/<int:id>', methods=['DELETE'])
def delete_customer_account(id):
    account = CustomerAccount.query.get_or_404(id)
    db.session.delete(account)
    db.session.commit()
    return jsonify({'message': 'Customer account deleted successfully'})

#4. CRUD Endpoints for Products
from app.models import Product

@app.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(name=data['name'], price=data['price'], stock=data.get('stock', 0))
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product created successfully'}), 201

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'stock': product.stock})

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.get_json()
    product.name = data['name']
    product.price = data['price']
    product.stock = data.get('stock', product.stock)
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/products', methods=['GET'])
def list_products():
    products = Product.query.all()
    return jsonify([{'id': product.id, 'name': product.name, 'price': product.price, 'stock': product.stock} for product in products])

#5. Order Processing Endpoints
from app.models import Order, OrderItem

@app.route('/orders', methods=['POST'])
def place_order():
    data = request.get_json()
    customer = Customer.query.get_or_404(data['customer_id'])
    new_order = Order(customer=customer)
    db.session.add(new_order)
    db.session.commit()
    
    for item in data['order_items']:
        product = Product.query.get_or_404(item['product_id'])
        order_item = OrderItem(order=new_order, product=product, quantity=item['quantity'])
        db.session.add(order_item)
    
    db.session.commit()
    return jsonify({'message': 'Order placed successfully'}), 201

@app.route('/orders/<int:id>', methods=['GET'])
def get_order(id):
    order = Order.query.get_or_404(id)
    order_items = [{'product_id': item.product_id, 'quantity': item.quantity} for item in order.order_items]
    return jsonify({'id': order.id, 'order_date': order.order_date, 'customer_id': order.customer_id, 'order_items': order_items})

@app.route('/orders/<int:id>/track', methods=['GET'])
def track_order(id):
    order = Order.query.get_or_404(id)
    return jsonify({'id': order.id, 'order_date': order.order_date, 'customer_id': order.customer_id, 'status': 'In Progress'})  # Add more detailed status tracking as needed

@app.route('/orders/<int:id>/cancel', methods=['POST'])
def cancel_order(id):
    order = Order.query.get_or_404(id)
    # Implement logic to check if the order can be canceled (e.g., not shipped yet)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'message': 'Order canceled successfully'})

@app.route('/orders/<int:id>/total', methods=['GET'])
def calculate_order_total(id):
    order = Order.query.get_or_404(id)
    total = sum(item.product.price * item.quantity for item in order.order_items)
    return jsonify({'order_id': order.id, 'total_price': total})

