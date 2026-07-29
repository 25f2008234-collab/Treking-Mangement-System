from flask import Flask, redirect , render_template,request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable = False)

class Trekking_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trekking_id = db.Column(db.Integer, db.ForeignKey('trekking_table.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)   

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Userprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_ = User.query.filter_by(email=email).first()

        if user_ and user_.password == password:
            if user_.role == "user":
                return "User dashboard"
            elif user_.role == "admin":
                return "Admin dashboard"
            elif user_.role == "staff":
                return "Staff dashboard"

        return "Invalid email or password!"

    return render_template('login.html')
    
@app.route('/signup',methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        ext_user = User.query.filter_by(email=email).first()
        if ext_user :
            return "you are already register. Please Login" 
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
            
        return redirect('/login')
    return render_template('signup.html')   
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/login')

@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/user")
def user_dashboard():
    return render_template("user_dashboard.html")

@app.route("/staff")
def staff_dashboard():
    return render_template("staff_dashboard.html")




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        exist_admin = User.query.filter_by(username="admin").first()
        if not exist_admin:
            admin_new = User(username = "admin", email = "admin@gmail.com", password= "admin123 ", role="admin")
            db.session.add(admin_new)
            db.session.commit()
    app.run(debug=True) 
