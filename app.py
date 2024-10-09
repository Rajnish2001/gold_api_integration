from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash, make_response
from flask_mysqldb import MySQL
import requests
from flask_bcrypt import Bcrypt
from models import *
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)


app.secret_key='fdkjshfhjsdfdskfdsfdcbsjdkfdsdf'


app.config['MYSQL_HOST'] = '144.76.3.17'  # Remote host
app.config['MYSQL_USER'] = 'varniraj_test1user'  # Remote user
app.config['MYSQL_PASSWORD'] = 'k@kQrbiLTfb5F6'  # Password
app.config['MYSQL_DB'] = 'varniraj_test1db'  # Database name


app.config['UPLOAD_FOLDER'] = r'bills'

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



mysql = MySQL(app)
bcrypt = Bcrypt(app)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM investor WHERE phone = %s", (phone,))
        user = cur.fetchone()
        cur.close()

        if user:
            # user[1] is assumed to be the hashed password
            if bcrypt.check_password_hash(user[1], password):
                session['user_id'] = user[0]  # Assuming user[0] is the ID
                session['fullname'] = user[2]  # Assuming user[2] is the fullname
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))  # Redirect to user list or dashboard
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('Phone number not found. Please check your phone number.', 'danger')

    return render_template('login.html')



@app.route('/api/login', methods=['POST'])
def login_api():
    # Get data from the POST request (JSON payload)
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return make_response(jsonify({'message': 'Email and password are required!'}), 400)

    email = data['email']
    password = data['password']

    # Query the database to find the user
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, fullname, password FROM investor WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    print("user===============",user)

    if not user:
        return make_response(jsonify({'message': 'User not found!'}), 404)

    user_id, fullname, hashed_password = user

    # Verify the password
    if  password == user[2]:
        # Login successful
        return make_response(jsonify({
            'message': 'Login successful!',
            'user_id': user_id,
            'fullname': fullname
        }), 200)
    else:
        # Incorrect password
        return make_response(jsonify({'message': 'Invalid password!'}), 401)
    

@app.route('/add_bill', methods=['GET', 'POST'])
def add_bill():
    # Fetch all investors for the dropdown
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, fullname FROM investor")  # Adjust to your table structure if needed
    investors = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        print("step-------------------------------------------1")
        # Get the selected investor ID
        investor_id = request.form.get('investor_id')

        # Check if the bill file is present in the request
        if 'bill_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        print("step-------------------------------------------2",investor_id)

        bill_file = request.files['bill_file']
        print("step-------------------------------------------3",bill_file)


        # Check if the file is valid
        if bill_file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        print("step-------------------------------------------4")

        if bill_file and allowed_file(bill_file.filename):
            filename = secure_filename(bill_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            print("Attempting to save file at:", file_path)
            try:
                bill_file.save(file_path)
                print("File saved successfully.")
            except Exception as e:
                print("Error saving file:", e)
                flash('Error saving file.', 'danger')
                return redirect(request.url)

            profit_amount = request.form.get('profit_amount')

            # Add the bill to the database
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO bills (investor_id, bill_file, profit_amount) VALUES (%s, %s, %s)",
                        (investor_id, file_path, profit_amount))
            mysql.connection.commit()
            cur.close()

            flash('Bill added successfully!', 'success')
            return redirect(url_for('investor_details', investor_id=investor_id))

    return render_template('add_bill.html', investors=investors)


@app.route('/update_passwords')
def update_passwords():
    # Step 1: Get all investors
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM investor")
    investors = cur.fetchall()
    
    for investor in investors:
        investor_id = investor[0]  # Assuming 'id' is the first column
        password = investor[1]     # Assuming 'password' is the second column

        # Step 2: Check if the password is hashed with SHA-256 (64 characters long)
        if len(password) == 64:
            # Step 3: Re-hash password using Werkzeug's hashing method
            new_password_hash = generate_password_hash(password)
            
            # Step 4: Update the password in the database
            cur.execute("UPDATE investor SET password = %s WHERE id = %s", (new_password_hash, investor_id))
            mysql.connection.commit()

    cur.close()

    return "Passwords have been updated where necessary."



@app.route('/users')
def users():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM testuser''')  # Replace 'users' with your table name
    users = cur.fetchall()
    cur.close()
    return render_template('users.html', users=users)


@app.route('/')
def dashboard():

    if 'logged_in' not in session:
        gold_price = get_gold_price()
        print("-----------------------------------------",gold_price)
        # return f"Welcome, {session['username']}!"
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM investor")
        investors = cur.fetchall()
        cur.close()

        # for i in investors:
        #     print("iiiiii",i)

        return render_template('dashboard.html', investors=investors, gold_price=gold_price)
    else:
        return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        investment = request.form['investment'] or 200.00  # Default investment if not provided
        nomineename = request.form['nomineename']
        nominee_phone = request.form['nominee_phone']

        # Hash the password
        hashed_password = password

        # Insert the investor into the database
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO investor (password, fullname, email, phone, investment, nomineename, nominee_phone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (hashed_password, fullname, email, phone, investment, nomineename, nominee_phone)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('dashboard'))  # Redirect to the login page after registration

    return render_template('register.html')


@app.route('/user_list')
def user_list():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM investor")  # Adjust to your table structure if needed
    rows = cur.fetchall()
    cur.close()

    investors = []
    for row in rows:
        investor = {
            'id': row[0],            
            'password': row[1],      
            'fullname': row[2],      
            'email': row[3],         
            'phone': row[4],         
            'investment': row[5],     
            'created_on': row[6],    
            'nomineename': row[7],    
            'nominee_phone': row[8],  
            'profit': row[9],        
            'used_gold': row[10],      
        }
        investors.append(investor)

    return render_template('user_list.html', investors=investors)


def get_gold_price():
    url = 'https://www.goldapi.io/api/XAU/USD'
    headers = {
        'x-access-token': 'goldapi-9ymlvsm21tc9o0-io'  # Your API token
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        print('data:==== ', data)
        
        if response.status_code == 200:
            return data['price']
        else:
            return None  # Handle error accordingly

    except Exception as e:
        return None  # Handle exception accordingly


@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    print("reset_password------",user_id)
    print("request.method------",request.method)
    pass


@app.route('/update_investor/<int:investor_id>', methods=['GET', 'POST'])
def update_investor(investor_id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        # Get data from the form
        fullname = request.form['fullname']
        email = request.form['email']
        phone = request.form['phone']
        investment = request.form['investment']
        nomineename = request.form['nomineename']
        nominee_phone = request.form['nominee_phone']
        password = request.form['password']  # New password field
        
        # Hash the new password if provided
        hashed_password = password
        
        # Update investor data in the database
        if hashed_password:
            cur.execute("""
                UPDATE investor
                SET fullname = %s, email = %s, phone = %s, investment = %s, nomineename = %s, nominee_phone = %s, password = %s
                WHERE id = %s
            """, (fullname, email, phone, investment, nomineename, nominee_phone, hashed_password, investor_id))
        else:
            cur.execute("""
                UPDATE investor
                SET fullname = %s, email = %s, phone = %s, investment = %s, nomineename = %s, nominee_phone = %s
                WHERE id = %s
            """, (fullname, email, phone, investment, nomineename, nominee_phone, investor_id))
        
        mysql.connection.commit()
        cur.close()
        
        flash('Investor data updated successfully!', 'success')
        return redirect(url_for('user_list'))  # Redirect to the investor details page

    else:
        # Fetch the existing investor data
        cur.execute("SELECT * FROM investor WHERE id = %s", (investor_id,))
        investor = cur.fetchone()
        cur.close()

        if investor:
            return render_template('update_investor.html', investor=investor)
        else:
            flash('Investor not found!', 'danger')
            return redirect(url_for('user_list'))  # Redirect to the user list




@app.route('/investor_details/<int:investor_id>', methods=['GET'])
def investor_details(investor_id):

    print("++++===========================================investor_id",investor_id)
    cur = mysql.connection.cursor()

    # Fetch the investor details from the database
    cur.execute("SELECT * FROM investor WHERE id = %s", (investor_id,))
    investor = cur.fetchone()  # Fetch the data for the specific investor
    cur.close()   

    # Check if the investor was found
    if investor is None:
        flash('Investor not found.', 'danger')
        return redirect(url_for('user_list'))  # Redirect to user list if not found

    return render_template('user_details.html', investor=investor)

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()  # This will remove all user session data
    return redirect(url_for('login'))

@app.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    pass


@app.route('/api/investors', methods=['POST'])
def create_investor():
    data = request.json
    fullname = data['fullname']
    email = data['email']
    phone = data['phone']
    password = data['password']
    nomineename = data['nomineename']
    nominee_phone = data['nominee_phone']
    investment = data.get('investment', 200.0)
    profit = data.get('profit', 0.0)
    used_gold = data.get('used_gold', 0.0)

    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO investor (password, fullname, email, phone, investment, created_on, nomineename, nominee_phone, profit, used_gold) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (password, fullname, email, phone, investment, datetime.utcnow(), nomineename, nominee_phone, profit, used_gold)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({"message": "Investor created successfully"}), 201


@app.route('/api/investors/<int:id>', methods=['GET'])
def get_investor(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM investor WHERE id = %s", (id,))
    investor = cur.fetchone()
    cur.close()

    if investor:
        investor_data = {
            'id': investor[0],
            'password': investor[1],
            'fullname': investor[2],
            'email': investor[3],
            'phone': investor[4],
            'investment': float(investor[5]),
            'created_on': investor[6],
            'nomineename': investor[7],
            'nominee_phone': investor[8],
            'profit': float(investor[9]),
            'used_gold': float(investor[10])
        }
        return jsonify(investor_data), 200
    else:
        return jsonify({"error": "Investor not found"}), 404



# @app.route('/users2', methods=['GET'])
# def get_investors():
#     # Open a cursor to perform database operations
#     cur = mysql.connection.cursor()
#     cur.execute("SELECT * FROM investor")  # Execute the query to fetch all investors
#     investors = cur.fetchall()  # Fetch all rows
#     cur.close()  # Close the cursor

#     # Create a list of investor data to return
#     investors_data = [
#         {
#             'id': investor[0],
#             'password': investor[1],
#             'fullname': investor[2],
#             'email': investor[3],
#             'phone': investor[4],
#             'investment': float(investor[5]),
#             'created_on': investor[6],
#             'nomineename': investor[7],
#             'nominee_phone': investor[8],
#             'profit': float(investor[9]),
#             'used_gold': float(investor[10])
#         }
#         for investor in investors
#     ]
#     return jsonify(investors_data), 200  # Return the investor data in JSON format

# # ------------------- UPDATE (PUT) -------------------
# @app.route('/api/investors/<int:id>', methods=['PUT'])
# def update_investor(id):
#     data = request.json
#     fullname = data['fullname']
#     email = data['email']
#     phone = data['phone']
#     password = data['password']
#     nomineename = data['nomineename']
#     nominee_phone = data['nominee_phone']
#     investment = data.get('investment', 200.0)
#     profit = data.get('profit', 0.0)
#     used_gold = data.get('used_gold', 0.0)

#     cur = mysql.connection.cursor()
#     cur.execute(
#         "UPDATE investor SET password = %s, fullname = %s, email = %s, phone = %s, investment = %s, nomineename = %s, nominee_phone = %s, profit = %s, used_gold = %s WHERE id = %s",
#         (password, fullname, email, phone, investment, nomineename, nominee_phone, profit, used_gold, id)
#     )
#     mysql.connection.commit()
#     cur.close()

#     return jsonify({"message": "Investor updated successfully"}), 200


# ------------------- DELETE (DELETE) -------------------
@app.route('/api/investors/<int:id>', methods=['DELETE'])
def delete_investor(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM investor WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Investor deleted successfully"}), 200


if __name__ == '__main__':
    app.run(debug=True)
