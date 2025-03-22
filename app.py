_from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(_name_)

# Secret key for sessions
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

mail = Mail(app)

# Ensure static folder works correctly
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# In-memory storage for users, products, and sales
users = {
    "admin": {"password": generate_password_hash("password123"), "role": "admin"}
}
products = []
sales = []
employees = []


# Authentication Check Helper
def is_logged_in():
    return 'user_id' in session


# Home Route (Dashboard)
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('dashboard.html', products=products, sales=sales)


# Add Product Route
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            name = request.form['name']
            category = request.form['category']
            price = float(request.form['price'])
            stock = int(request.form.get('stock', 0))
            products.append({"name": name, "category": category, "price": price, "stock": stock})
            flash('Product added successfully!', 'success')
            return redirect(url_for('product_list'))
        except ValueError:
            flash('Invalid input. Please check your data.', 'danger')
    return render_template('add_product.html')


# View Products Route
@app.route('/products')
def product_list():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('products.html', products=products)


# Add Sales Route
@app.route('/add_sales', methods=['GET', 'POST'])
def add_sales():
    if not is_logged_in():
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            sale = {
                'product_name': request.form['product_name'],
                'salesperson_id': request.form['salesperson_id'],
                'customer_id': request.form['customer_id'],
                'sale_date': request.form['sale_date'],
                'quantity': int(request.form['quantity']),
                'total_amount': float(request.form['total_amount'])
            }
            sales.append(sale)
            flash('Sales record added successfully!', 'success')
            return redirect(url_for('sales_performance'))
        except ValueError:
            flash('Invalid input. Please check your data.', 'danger')
    return render_template('add_sales.html')


# Sales Performance Route
@app.route('/sales_performance')
def sales_performance():
    if not is_logged_in():
        return redirect(url_for('login'))
    return render_template('sales_performance.html', sales=sales)


# Low Stock Checker Route
@app.route('/lowstocks', methods=['GET', 'POST'])
def lowstocks():
    if not is_logged_in():
        return redirect(url_for('login'))

    low_stock_threshold = 5  # Default threshold
    if request.method == 'POST':
        try:
            low_stock_threshold = int(request.form['threshold'])
        except ValueError:
            flash('Invalid input. Please enter a valid number.', 'danger')

    low_stock_products = [p for p in products if p['stock'] < low_stock_threshold]
    return render_template('lowstocks.html', low_stock_products=low_stock_products, threshold=low_stock_threshold)


# Improve Sales Tips Route
@app.route('/improve_sales')
def improve_sales():
    if not is_logged_in():
        return redirect(url_for('login'))
    sales_tips = [
        {"title": "Upselling Techniques", "link": "https://example.com/upselling"},
        {"title": "Customer Retention Strategies", "link": "https://example.com/customer-retention"}
    ]
    return render_template('improve_sales.html', sales_tips=sales_tips)


# Feedback Route (with Email)
@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback_message = request.form['feedback']
        try:
            msg = Message("User Feedback", sender=app.config['MAIL_USERNAME'], recipients=[app.config['MAIL_USERNAME']])
            msg.body = f"Name: {name}\nEmail: {email}\nFeedback: {feedback_message}"
            mail.send(msg)
            flash('Thank you for your feedback!', 'success')
        except Exception as e:
            flash(f'Error sending feedback: {e}', 'danger')
    return render_template('feedback.html')


# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if username in users:
            flash('Username already exists.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            users[username] = {"password": generate_password_hash(password), "role": "user"}
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


# Profit and Loss Calculation
@app.route('/profit_and_loss', methods=['GET', 'POST'])
def profit_and_loss():
    if not is_logged_in():
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            total_sales = float(request.form['total_sales'])
            total_costs = float(request.form['total_costs'])
            profit_or_loss = total_sales - total_costs
            return render_template('profit_and_loss.html', total_sales=total_sales, total_costs=total_costs, profit_or_loss=profit_or_loss)
        except ValueError:
            flash('Invalid input. Please enter valid numbers.', 'danger')

    return render_template('profit_and_loss.html', total_sales=None, total_costs=None, profit_or_loss=None)


# Ensure the app runs on the correct port (for Render deployment)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
