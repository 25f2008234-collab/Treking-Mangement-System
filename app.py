from flask import Flask, redirect , render_template,request, session 
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "trekking_management_system"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable = False)
    status = db.Column(db.String(20), default="active")

class Trekking_table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    available_slots = db.Column(db.Integer, default=20)
    status = db.Column(db.String(20), default="Open")
    progress = db.Column(db.String(20), default="Not Started")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trekking_id = db.Column(db.Integer, db.ForeignKey('trekking_table.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User')
    trek = db.relationship('Trekking_table')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    user = db.relationship('User')

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
    status = db.Column(db.String(20), default="Active")
    treks = db.relationship('Trekking_table', backref='staff', lazy=True)

class Userprofile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    

@app.route("/")
def home():
    return render_template("index.html")
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user_ = User.query.filter_by(email=email).first()

        if user_ is None:
            return "NO account found with this email."

        if user_.password != password:
            return "Incorrect Password."

        if user_.status == "Blocked":
            return "Your account has been blocked."
        session["user_id"] = user_.id
        session["username"] = user_.username
        session["role"] = user_.role

        if user_.role == "admin":
            return redirect("/admin_dashboard")

        elif user_.role == "staff":
            return redirect("/staff_dashboard")

        else:
            return redirect("/user")

    return render_template("login.html")
    
@app.route('/signup',methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user :
            return "you are already register. Please Login" 
        new_user = User(username=username, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        if role == "staff":
            new_staff = Staff(name=username, role="staff")
            db.session.add(new_staff)
            db.session.commit()
            
        return redirect('/login')
    return render_template('signup.html')   
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')

# Admin

@app.route("/admin_dashboard")
def admin():
    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    total_users = User.query.count()
    total_treks = Trekking_table.query.count()
    total_staff = Staff.query.count()
    total_bookings = Booking.query.count()
    return render_template("Admin/admin_dashboard.html", total_users=total_users, total_treks=total_treks, total_staff=total_staff, total_bookings=total_bookings)

@app.route("/create_trek", methods=['GET', 'POST'])
def create_trek():
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        description = request.form["description"]
        duration = request.form["duration"]

        user_id = session.get('user_id')

        new_trek = Trekking_table(name=name, location=location, description=description, duration=duration, user_id=user_id)
        db.session.add(new_trek)
        db.session.commit()

        return redirect("/treks")

    return render_template('Admin/create_trek.html')

@app.route("/update_trek/<int:trek_id>", methods=['GET', 'POST'])
def update_trek(trek_id):
    trek = Trekking_table.query.get_or_404(trek_id)
    if request.method == 'POST':
        trek.name = request.form['name']
        trek.location = request.form['location']
        trek.description = request.form['description']
        trek.duration = request.form['duration']
        db.session.commit()
        return redirect("/treks")
    return render_template('Admin/update_trek.html', trek=trek)

@app.route("/remove_trek/<int:trek_id>")
def remove_trek(trek_id):
    trek = Trekking_table.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    return redirect("/treks")

@app.route("/treks")
def list_treks():
    treks = Trekking_table.query.all()
    return render_template('Admin/treks.html', treks=treks)

@app.route("/book_trek/<int:trek_id>")
def book_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.status != "Open":
        return "This trek is closed. Booking is not allowed."

    if trek.available_slots <= 0:
        return "No slots available for this trek."

    booking = Booking.query.filter_by(
        user_id=session["user_id"],
        trekking_id=trek_id
    ).first()

    if booking:
        return "You have already booked this trek."

    new_booking = Booking(user_id=session["user_id"],trekking_id=trek_id,booking_date=datetime.now())

    db.session.add(new_booking)

    trek.available_slots = trek.available_slots - 1
    db.session.commit()
    return redirect("/history")

@app.route("/block_user/<int:user_id>")
def block_user(user_id):

    user = User.query.get_or_404(user_id)

    if user.role == "admin":
        return "Admin account cannot be blocked."

    user.status = "Blocked"

    db.session.commit()

    return redirect("/users")


@app.route("/unblock_user/<int:user_id>")
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.status = "Active"
    db.session.commit()
    return redirect("/users")

@app.route("/staff", methods=['GET', 'POST'])
def staff():
    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']

        new_staff = Staff(name=name, role=role)
        db.session.add(new_staff)
        db.session.commit()

        return redirect("/staff")

    staff_members = Staff.query.all()

    return render_template('Admin/staff.html', staff_members=staff_members)

@app.route("/approve_staff", methods=['GET', 'POST'])
def approve_staff():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        staff_member = Staff.query.get(staff_id)
        if staff_member:
            staff_member.role = "approved"
            db.session.commit()
            return redirect('Admin/admin_dashboard')
        else:
            return "Staff member not found."
    staff_members = Staff.query.all()
    return render_template('Admin/approve_staff.html', staff_members=staff_members)

@app.route("/block_staff/<int:staff_id>")
def block_staff(staff_id):

    staff = Staff.query.get_or_404(staff_id)

    staff.status = "Blocked"

    db.session.commit()

    return redirect("/staff")

@app.route("/unblock_staff/<int:staff_id>")
def unblock_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    staff.status = "Active"
    db.session.commit()
    return redirect("/staff")

@app.route("/remove_staff/<int:staff_id>")
def remove_staff(staff_id):

    staff = Staff.query.get_or_404(staff_id)

    db.session.delete(staff)

    db.session.commit()

    return redirect("/staff")

@app.route("/assign_trek", methods=['GET', 'POST'])

def assign_trek():
    if request.method == "POST":
        staff_id = request.form["staff_id"]
        trek_id = request.form["trek_id"]

        trek = Trekking_table.query.get(trek_id)

        if trek:
            trek.staff_id = staff_id
            db.session.commit()

        return redirect("/treks")

    staff_members = Staff.query.all()
    treks = Trekking_table.query.all()

    return render_template(
        "Admin/assign_trek.html",
        staff_members=staff_members,
        treks=treks
    )

@app.route("/bookings")
def bookings():

    bookings = Booking.query.all()

    return render_template(
        "Admin/booking.html",
        bookings=bookings)

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template(
        "Admin/history.html",
        bookings=bookings
    )


@app.route("/users")
def manage_users():
    users = User.query.all()
    return render_template('Admin/manage_users.html', users=users)

@app.route("/search", methods=["GET", "POST"])
def search():

    results = []
    search_type = ""

    if request.method == "POST":

        keyword = request.form["keyword"]
        search_type = request.form["type"]

        if search_type == "trek":
            results = Trekking_table.query.filter(
                Trekking_table.name.contains(keyword)
            ).all()

        elif search_type == "staff":
            results = Staff.query.filter(
                Staff.name.contains(keyword)
            ).all()

        else:
            results = User.query.filter(
                User.username.contains(keyword)
            ).all()

    return render_template("Admin/search.html",results=results,search_type=search_type)

# Staff

@app.route("/staff_dashboard")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    if not staff:
        return "Staff record not found."

    assigned_treks = Trekking_table.query.filter_by(staff_id=staff.id).all()

    total_treks = len(assigned_treks)

    total_participants = 0

    for trek in assigned_treks:
        count = Booking.query.filter_by(trekking_id=trek.id).count()
        total_participants += count

    return render_template("Staff/staff_dashboard.html",staff=staff,total_treks=total_treks,total_participants=total_participants)

@app.route("/edit_staff_profile/<int:staff_id>", methods=["GET", "POST"])
def edit_staff_profile(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    if request.method == "POST":
        staff.name = request.form["name"]
        staff.role = request.form["role"]
        db.session.commit()
        return redirect("/staff")
    return render_template("Staff/edit_staff_profile.html", staff=staff)

@app.route("/participants")
def participants():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    treks = Trekking_table.query.filter_by(staff_id=staff.id).all()

    participant_list = []

    for trek in treks:

        bookings = Booking.query.filter_by(trekking_id=trek.id).all()

        for booking in bookings:

            user = User.query.get(booking.user_id)

            participant_list.append({
                "trek_name": trek.name,
                "username": user.username,
                "email": user.email,
                "booking_date": booking.booking_date
            })

    return render_template("Staff/participants.html",participant_list=participant_list)

@app.route("/update_progress/<int:trek_id>", methods=["GET", "POST"])
def update_progress(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        trek.progress = request.form["progress"]

        db.session.commit()

        return redirect("/my_treks")

    return render_template("Staff/update_progress.html",trek=trek)

@app.route("/update_status/<int:trek_id>", methods=["GET","POST"])
def update_status(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        trek.status = request.form["status"]

        db.session.commit()

        return redirect("/my_treks")

    return render_template("Staff/update_status.html",trek=trek)


@app.route("/my_treks")
def my_treks():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    if not staff:
        return "Staff record not found."

    treks = Trekking_table.query.filter_by(staff_id=staff.id).all()

    return render_template("Staff/my_trek.html",treks=treks)

@app.route("/update_slots/<int:trek_id>", methods=["GET", "POST"])
def update_slots(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(name=session["username"]).first()

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        trek.available_slots = request.form["slots"]

        db.session.commit()

        return redirect("/my_treks")

    return render_template("Staff/update_slots.html",trek=trek)

# User

@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("User/user_dashboard.html")

@app.route("/edit_profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["user_id"] != user_id:
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]

        db.session.commit()
        session["username"] = user.username
        return redirect("/user")
    
    return render_template("User/edit_profile.html", user=user)

@app.route("/browse_treks")
def browse_treks():
    if "user_id" not in session:
        return redirect("/login")
    treks = Trekking_table.query.all()
    return render_template("User/browse_treks.html", treks=treks)

@app.route("/trek_details/<int:trek_id>")
def trek_details(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    trek = Trekking_table.query.get_or_404(trek_id)

    return render_template("User/view_trek.html",trek=trek) 

@app.route("/my_bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()

    return render_template("User/my_bookings.html", bookings=bookings)

@app.route("/search_treks", methods=["GET", "POST"])
def search_treks():

    if "user_id" not in session:
        return redirect("/login")

    treks = Trekking_table.query.all()

    if request.method == "POST":

        search = request.form["search"]

        treks = Trekking_table.query.filter(
            (Trekking_table.name.contains(search)) |
            (Trekking_table.location.contains(search))
        ).all()

    return render_template(
        "User/search_treks.html",
        treks=treks
    )



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        exist_admin = User.query.filter_by(username="admin").first()
        if not exist_admin:
            admin_new = User(username = "admin", email = "admin@gmail.com", password= "admin123", role="admin")
            db.session.add(admin_new)
            db.session.commit()
    app.run(debug=True) 
