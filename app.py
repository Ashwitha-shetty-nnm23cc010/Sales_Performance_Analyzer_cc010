from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import os
#import openai
#import requests  # Add this import for sending SMS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Use environment variable
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Use environment variable

mail = Mail(app)

# Configure OpenAI API key
openai.api_key = 'your_openai_api_key'

# Ensure static folder is correctly configured
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# In-memory storage for users, products, and sales
users = {
    "admin": {"password": generate_password_hash("password123"), "role": "admin"}
}
products = []
sales = []

# Routes
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', products=products, sales=sales)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = float(request.form['price'])
        stock = int(request.form.get('stock', 0))
        products.append({"name": name, "category": category, "price": price, "stock": stock})
        flash('Product added successfully!', 'success')
        return redirect(url_for('product_list'))  # Redirect to avoid duplicate submissions
    return render_template('add_product.html')
@app.route('/add_sales', methods=['GET', 'POST'])
def add_sales():
    if 'user_id' not in session:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        sale = {
            'product_name': request.form['product_name'],
            'product_id': request.form['product_id'],
            'salesperson_id': request.form['salesperson_id'],
            'customer_id': request.form['customer_id'],
            'sale_date': request.form['sale_date'],
            'quantity': request.form['quantity'],
            'total_amount': request.form['total_amount'],
            'amount': request.form['amount']
        }
        sales.append(sale)
        flash('Sales record added successfully!', 'success')
        return redirect(url_for('sales_performance'))
    return render_template('add_sales.html')

@app.route('/products')
def product_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('products.html', products=products)

@app.route('/sales_performance')
def sales_performance():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('sales_performance.html', sales=sales)

@app.route('/lowstocks', methods=['GET', 'POST'])
def lowstocks():
    if 'user_id' not in session:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))

    low_stock_threshold = 5  # Default threshold
    low_stock_products = []

    if request.method == 'POST':
        try:
            low_stock_threshold = int(request.form['threshold'])
        except ValueError:
            flash('Please enter a valid number.', 'danger')

    low_stock_products = [p for p in products if p.get('stock', 0) < low_stock_threshold]

    return render_template('lowstocks.html', low_stock_products=low_stock_products, threshold=low_stock_threshold)

@app.route('/improve_sales')
def improve_sales():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    sales_tips = [
        {"title": "Upselling Techniques", "link": "https://example.com/upselling-techniques"},
        {"title": "Effective Sales Pitching", "link": "https://example.com/sales-pitching"},
        {"title": "Customer Retention Strategies", "link": "https://example.com/customer-retention"},
        {"title": "Leveraging Social Media for Sales", "link": "https://example.com/social-media-sales"},
        {"title": "Data-Driven Sales Insights", "link": "https://example.com/data-driven-sales"}
    ]
    return render_template('improve_sales.html', sales_tips=sales_tips)

@app.route('/improve_sales_resources', methods=['GET', 'POST'])
def improve_sales_resources():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        sender_email = os.getenv('SENDER_EMAIL')  # Use environment variable for sender email
        msg = Message("Contact Form Submission", sender=sender_email, recipients=[sender_email])
        msg.body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        mail.send(msg)
        flash('Message sent successfully!', 'success')
    return render_template('improve_sales_resources.html')  # Updated template name

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        feedback_message = request.form['feedback']
        sender_email = os.getenv('SENDER_EMAIL')  # Use environment variable for sender email
        msg = Message("User Feedback", sender=sender_email, recipients=[sender_email])
        msg.body = f"Name: {name}\nEmail: {email}\nFeedback: {feedback_message}"
        mail.send(msg)

        # Simulate sending a normal text message
        text_message = f"Feedback from {name} ({email}): {feedback_message}"
        print(f"Text Message: {text_message}")  # Log the text message to the console

        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if username in users:
            flash('Username already exists', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match', 'danger')
        else:
            users[username] = {"password": generate_password_hash(password), "role": "user"}
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/profit_and_loss', methods=['GET', 'POST'])
def profit_and_loss():
    if request.method == 'POST':
        # Collect user input from the form
        total_sales = float(request.form['total_sales'])
        total_costs = float(request.form['total_costs'])
        
        # Calculate profit or loss
        profit_or_loss = total_sales - total_costs
        
        # Pass results back to the template
        return render_template(
            'profit_and_loss.html',
            total_sales=total_sales,
            total_costs=total_costs,
            profit_or_loss=profit_or_loss
        )
    
    # Render the page with an empty form for GET request
    return render_template('profit_and_loss.html', total_sales=None, total_costs=None, profit_or_loss=None)

         # In-memory storage for employee details
employees = []

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'user_id' not in session:
        flash('Access denied.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Collect employee details from the form
        name = request.form['name']
        department = request.form['department']
        designation = request.form['designation']
        salary = float(request.form['salary'])
        # Store employee details
        employees.append({"name": name, "department": department, "designation": designation, "salary": salary})
        flash('Employee added successfully!', 'success')
        return redirect(url_for('view_employees'))
    return render_template('add_employee.html')

@app.route('/view_employees')
def view_employees():
    if 'user_id' not in session:  # Check if user is logged in
        flash('Access denied.', 'danger')  # Display error message if not logged in
        return redirect(url_for('login'))  # Redirect to login page

    # Debugging: Print the directory contents of 'templates' to verify file visibility
    import os
    print("Templates Directory Contents:", os.listdir('templates'))

    # Render the template with the employees list passed as a parameter
    return render_template('view_employees.html', employees=employees)
if __name__ == '__main__':
    app.run(debug=True)
