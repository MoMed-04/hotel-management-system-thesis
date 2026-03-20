from flask import Blueprint, render_template, request, redirect, url_for
from models.customer_model import get_all_customers, add_customer

# Create the blueprint
customer_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customer_bp.route('/')
def index():
    customers = get_all_customers()
    return render_template('customers/customers_list.html', customers=customers)

@customer_bp.route('/add', methods=['POST'])
def create():
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    email = request.form.get('email')
    
    add_customer(full_name, phone, email)
    
    return redirect(url_for('customers.index'))