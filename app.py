from flask import Flask, redirect , render_template,request, session 
from datetime import datetime , date
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
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    difficulty = db.Column(db.String(20), default="Easy")
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'))
    available_slots = db.Column(db.Integer, default=20)  
    status = db.Column(db.String(20), default="Upcoming")
    progress = db.Column(db.String(20), default="Not Started")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trekking_id = db.Column(db.Integer, db.ForeignKey('trekking_table.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    booking_status = db.Column(db.String(20), default="Booked")
    payment_status = db.Column(db.String(20), default="Pending")
    user = db.relationship('User')
    trek = db.relationship('Trekking_table')


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="pending")
    treks = db.relationship('Trekking_table', backref='staff', lazy=True)

class TrekChangeRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    trek_id = db.Column(db.Integer, db.ForeignKey('trekking_table.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)

    change_type = db.Column(db.String(20), nullable=False)
    requested_value = db.Column(db.String(50), nullable=False)

    status = db.Column(db.String(20), default="Pending")

    request_date = db.Column(db.DateTime, default=datetime.now)

    trek = db.relationship('Trekking_table')
    staff = db.relationship('Staff')




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

            staff = Staff.query.filter_by(name=user_.username).first()

            if not staff:
                return "Staff record not found."

            if staff.status == "pending" or staff.status == "Pending":
                return "Your account is waiting for Admin approval."

            if staff.status == "Rejected":
                return "Your staff registration was rejected."

            if staff.status == "Blocked":
                return "Your staff account has been blocked."

            if staff.status != "Active":
                return "Your staff account is not active."

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
            new_staff = Staff(name=username, role="staff", status="pending")
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
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        description = request.form["description"]
        duration = int(request.form["duration"])
        
        if duration <= 0:
            return "Duration must be greater than 0."

        difficulty = request.form.get("difficulty", "").strip()

        if difficulty == "":
            return "Difficulty is required."

        if difficulty not in ["Easy", "Medium", "Hard"]:
            return "Invalid difficulty."

        available_slots = int(request.form["available_slots"])

        start_date = datetime.strptime(request.form["start_date"],"%Y-%m-%d").date()

        end_date = datetime.strptime(request.form["end_date"],"%Y-%m-%d").date()

        if start_date <= date.today():
            return "Start date must be after today."

        if end_date < start_date:
            return "End date cannot be before start date."

        if available_slots <= 0:
            return "Available slots must be greater than 0."


        existing_trek = Trekking_table.query.filter_by(name=name).first()

        if existing_trek:
            return "A trek with this name already exists."

        user_id = session.get('user_id')

        new_trek = Trekking_table(name=name, location=location, description=description, duration=duration, start_date=start_date, end_date=end_date, difficulty=difficulty, available_slots=available_slots, status="Upcoming", user_id=user_id)
        db.session.add(new_trek)
        db.session.commit()

        return redirect("/treks")

    return render_template('Admin/create_trek.html')

@app.route("/update_trek/<int:trek_id>", methods=["GET", "POST"])
def update_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    trek = Trekking_table.query.get_or_404(trek_id)

    if request.method == "POST":

        name = request.form["name"].strip()
        location = request.form["location"].strip()
        description = request.form["description"].strip()

        if name == "":
            return "Trek name is required."

        if location == "":
            return "Location is required."

        if description == "":
            return "Description is required."

        existing_trek = Trekking_table.query.filter(
            Trekking_table.name == name,
            Trekking_table.id != trek.id
        ).first()

        if existing_trek:
            return "A trek with this name already exists."

        try:
            duration = int(request.form["duration"])
            available_slots = int(request.form["available_slots"])
        except:
            return "Duration and slots must be valid numbers."

        if duration <= 0:
            return "Duration must be greater than 0."

        if available_slots <= 0:
            return "Available slots must be greater than 0."

        difficulty = request.form.get("difficulty", "").strip()

        if difficulty == "":
            return "Difficulty is required."

        if difficulty not in ["Easy", "Medium", "Hard"]:
            return "Invalid difficulty."

        try:
            start_date = datetime.strptime(
                request.form["start_date"],
                "%Y-%m-%d"
            ).date()

            end_date = datetime.strptime(
                request.form["end_date"],
                "%Y-%m-%d"
            ).date()

        except:
            return "Please enter valid dates."

        if start_date <= date.today():
            return "Start date must be after today."

        if end_date < start_date:
            return "End date cannot be before start date."

        booked_count = Booking.query.filter_by(
            trekking_id=trek.id,
            booking_status="Booked"
        ).count()

        if available_slots < booked_count:
            return "Available slots cannot be less than booked participants."

        if trek.staff_id:

            assigned_treks = Trekking_table.query.filter(
                Trekking_table.staff_id == trek.staff_id,
                Trekking_table.id != trek.id
            ).all()

            for assigned_trek in assigned_treks:

                if start_date <= assigned_trek.end_date and end_date >= assigned_trek.start_date:
                    return "These dates overlap with another trek assigned to the same staff member."

        trek.name = name
        trek.location = location
        trek.description = description
        trek.duration = duration
        trek.start_date = start_date
        trek.end_date = end_date
        trek.difficulty = difficulty
        trek.available_slots = available_slots

        db.session.commit()

        return redirect("/treks")

    return render_template(
        "Admin/update_trek.html",
        trek=trek
    )

@app.route("/remove_trek/<int:trek_id>")
def remove_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    trek = Trekking_table.query.get_or_404(trek_id)

    bookings = Booking.query.filter_by(
        trekking_id=trek.id
    ).all()

    for booking in bookings:
        db.session.delete(booking)

    db.session.delete(trek)

    db.session.commit()

    return redirect("/treks")

@app.route("/treks")
def list_treks():
    if "user_id" not in session:
        return redirect("/login")
    
    if session.get("role") != "admin":
        return "Access Denied"

    treks = Trekking_table.query.all()
    return render_template('Admin/treks.html', treks=treks)


@app.route("/book_trek/<int:trek_id>")
def book_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "user":
        return "Access Denied"

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.status != "Open":
        return "This trek is not open for booking."

    if trek.start_date <= date.today() and trek.status == "Upcoming":
        return "This trek is not available for booking yet."

    if trek.available_slots <= 0:
        return "No slots available for this trek."

    booking = Booking.query.filter_by(
        user_id=session["user_id"],
        trekking_id=trek_id
    ).filter(
        Booking.booking_status != "Cancelled"
    ).first()

    if booking:
        return "You have already booked this trek."

    new_booking = Booking(
        user_id=session["user_id"],
        trekking_id=trek_id,
        booking_date=datetime.now(),
        booking_status="Booked",
        payment_status="Paid"
    )

    db.session.add(new_booking)

    trek.available_slots -= 1

    db.session.commit()

    return redirect("/my_bookings")


@app.route("/block_user/<int:user_id>")
def block_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    if user.role == "admin":
        return "Admin account cannot be blocked."

    user.status = "Blocked"

    db.session.commit()

    return redirect("/users")


@app.route("/unblock_user/<int:user_id>")
def unblock_user(user_id):
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)
    user.status = "Active"
    db.session.commit()
    return redirect("/users")

@app.route("/staff")
def staff():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    staff_members = Staff.query.all()

    return render_template(
        "Admin/staff.html",
        staff_members=staff_members
    )

@app.route("/approve_staff", methods=["GET", "POST"])
def approve_staff():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    if request.method == "POST":

        staff_id = int(request.form["staff_id"])
        action = request.form["action"]

        staff_member = Staff.query.get(staff_id)

        if not staff_member:
            return "Staff member not found."

        if action == "approve":

            if staff_member.status not in ["Pending", "pending", "Rejected"]:
                return "This staff member cannot be approved."

            staff_member.status = "Active"

        elif action == "reject":

            if staff_member.status not in ["Pending", "pending"]:
                return "This staff member cannot be rejected."

            staff_member.status = "Rejected"

        else:
            return "Invalid action."

        db.session.commit()

        return redirect("/approve_staff")

    staff_members = Staff.query.filter(
        (Staff.status == "Pending") |
        (Staff.status == "pending") |
        (Staff.status == "Rejected")
    ).all()

    return render_template(
        "Admin/approve_staff.html",
        staff_members=staff_members
    )

@app.route("/trek_change_requests")
def trek_change_requests():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    requests = TrekChangeRequest.query.filter_by(
        status="Pending"
    ).all()

    return render_template(
        "Admin/trek_change_requests.html",
        requests=requests
    )

@app.route("/approve_trek_change/<int:request_id>")
def approve_trek_change(request_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    change_request = TrekChangeRequest.query.get_or_404(request_id)

    if change_request.status != "Pending":
        return "This request has already been processed."

    trek = Trekking_table.query.get(change_request.trek_id)

    if not trek:
        return "Trek not found."

    if change_request.change_type == "slots":

        new_slots = int(change_request.requested_value)

        booked_count = Booking.query.filter_by(
            trekking_id=trek.id,
            booking_status="Booked"
        ).count()

        if new_slots < booked_count:
            return "Requested slots are less than booked participants."

        trek.available_slots = new_slots

    elif change_request.change_type == "progress":

        trek.progress = change_request.requested_value

        if trek.progress == "Completed":

            trek.status = "Closed"

            bookings = Booking.query.filter_by(
                trekking_id=trek.id,
                booking_status="Booked"
            ).all()

            for booking in bookings:
                booking.booking_status = "Completed"

    elif change_request.change_type == "status":

        new_status = change_request.requested_value

        if new_status == "Closed":

            if trek.progress != "Completed":
                return "Trek must be completed before closing."

            trek.status = "Closed"

            bookings = Booking.query.filter_by(
                trekking_id=trek.id,
                booking_status="Booked"
            ).all()

            for booking in bookings:
                booking.booking_status = "Completed"

        elif new_status == "Open":

            if trek.progress == "Completed":
                return "A completed trek cannot be opened."

            trek.status = "Open"

    else:
        return "Invalid change type."

    change_request.status = "Approved"

    db.session.commit()

    return redirect("/trek_change_requests")

@app.route("/reject_trek_change/<int:request_id>")
def reject_trek_change(request_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    change_request = TrekChangeRequest.query.get_or_404(request_id)

    if change_request.status != "Pending":
        return "This request has already been processed."

    change_request.status = "Rejected"

    db.session.commit()

    return redirect("/trek_change_requests")

@app.route("/block_staff/<int:staff_id>")
def block_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    staff = Staff.query.get_or_404(staff_id)

    if staff.status == "Rejected":
        return "Rejected staff cannot be blocked."

    staff.status = "Blocked"

    db.session.commit()

    return redirect("/staff")

@app.route("/unblock_staff/<int:staff_id>")
def unblock_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    staff = Staff.query.get_or_404(staff_id)

    if staff.status != "Blocked":
        return "This staff member is not blocked."

    staff.status = "Active"

    db.session.commit()

    return redirect("/staff")

@app.route("/remove_staff/<int:staff_id>")
def remove_staff(staff_id):
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    staff = Staff.query.get_or_404(staff_id)

    db.session.delete(staff)

    db.session.commit()

    return redirect("/staff")

@app.route("/assign_trek", methods=["GET", "POST"])
def assign_trek():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    if request.method == "POST":

        staff_id = int(request.form["staff_id"])
        trek_id = int(request.form["trek_id"])

        staff_member = Staff.query.get(staff_id)
        trek = Trekking_table.query.get(trek_id)

        if not staff_member:
            return "Staff member not found."

        if not trek:
            return "Trek not found."

        if staff_member.status != "Active":
            return "This staff member is not active."

        assigned_treks = Trekking_table.query.filter(
    Trekking_table.staff_id == staff_id,
    Trekking_table.id != trek.id
).all()

        for assigned_trek in assigned_treks:

            if trek.start_date <= assigned_trek.end_date and trek.end_date >= assigned_trek.start_date:
                return "This staff member already has a trek during these dates."

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

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    bookings = Booking.query.all()

    return render_template(
        "Admin/booking.html",
        bookings=bookings
    )

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    bookings = Booking.query.filter_by(
        user_id=session["user_id"]
    ).all()

    return render_template("Admin/history.html",bookings=bookings)


@app.route("/users")
def manage_users():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"
    
    users = User.query.all()
    return render_template('Admin/manage_users.html', users=users)

@app.route("/search", methods=["GET", "POST"])
def search():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "admin":
        return "Access Denied"

    results = []
    search_type = ""

    if request.method == "POST":

        keyword = request.form["keyword"]
        search_type = request.form["type"]

        if search_type == "trek":

            if keyword.isdigit():

                results = Trekking_table.query.filter(
                    Trekking_table.id == int(keyword)
                ).all()

            else:

                results = Trekking_table.query.filter(
                    Trekking_table.name.contains(keyword)
                ).all()

        elif search_type == "staff":

            if keyword.isdigit():

                results = Staff.query.filter(
                    Staff.id == int(keyword)
                ).all()

            else:

                results = Staff.query.filter(
                    Staff.name.contains(keyword)
                ).all()

        elif search_type == "user":

            if keyword.isdigit():

                results = User.query.filter(
                    User.id == int(keyword)
                ).all()

            else:

                results = User.query.filter(
                    User.username.contains(keyword)
                ).all()

    return render_template(
        "Admin/search.html",
        results=results,
        search_type=search_type
    )

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

    if "user_id" not in session:
        return redirect("/login")

    staff = Staff.query.get_or_404(staff_id)

    if session.get("role") == "staff":

        if staff.name != session["username"]:
            return "Access Denied"

    elif session.get("role") == "admin":

        pass

    else:
        return "Access Denied"

    if request.method == "POST":

        name = request.form["name"].strip()

        if name == "":
            return "Name is required."

        existing_staff = Staff.query.filter(
            Staff.name == name,
            Staff.id != staff.id
        ).first()

        if existing_staff:
            return "A staff member with this name already exists."

        staff.name = name

        if session.get("role") == "admin":
            staff.role = request.form["role"]

        db.session.commit()

        if session.get("role") == "staff":
            session["username"] = staff.name
            return redirect("/staff_dashboard")

        return redirect("/staff")

    return render_template(
        "Staff/edit_staff_profile.html",
        staff=staff
    )

@app.route("/participants")
def participants():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    treks = Trekking_table.query.filter_by(
        staff_id=staff.id
    ).all()

    participant_list = []

    for trek in treks:

        bookings = Booking.query.filter_by(
            trekking_id=trek.id,
            booking_status="Booked"
        ).all()

        for booking in bookings:

            user = User.query.get(booking.user_id)

            if user:
                participant_list.append({
                    "trek_name": trek.name,
                    "username": user.username,
                    "email": user.email,
                    "booking_date": booking.booking_date
                })

    return render_template(
        "Staff/participants.html",
        participant_list=participant_list
    )

@app.route("/update_progress/<int:trek_id>", methods=["GET", "POST"])
def update_progress(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        progress = request.form.get("progress")

        if progress not in ["Not Started", "Started", "Ongoing", "Completed"]:
            return "Invalid progress."

        if progress == "Completed":

            booked_count = Booking.query.filter_by(
                trekking_id=trek.id,
                booking_status="Booked"
            ).count()

            if booked_count > 0:
                pass

        existing_request = TrekChangeRequest.query.filter_by(
            trek_id=trek.id,
            change_type="progress",
            status="Pending"
        ).first()

        if existing_request:
            return "A progress change request is already waiting for Admin approval."

        new_request = TrekChangeRequest(
            trek_id=trek.id,
            staff_id=staff.id,
            change_type="progress",
            requested_value=progress,
            status="Pending"
        )

        db.session.add(new_request)
        db.session.commit()

        return redirect("/my_treks")

    return render_template(
        "Staff/update_progress.html",
        trek=trek
    )


@app.route("/update_status/<int:trek_id>", methods=["GET", "POST"])
def update_status(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        status = request.form.get("status")

        if status not in ["Open", "Closed"]:
            return "Invalid trek status."

        if status == "Closed" and trek.progress != "Completed":
            return "A trek can be closed only after it is completed."

        if status == "Open" and trek.progress == "Completed":
            return "A completed trek cannot be opened again."

        existing_request = TrekChangeRequest.query.filter_by(
            trek_id=trek.id,
            change_type="status",
            status="Pending"
        ).first()

        if existing_request:
            return "A status change request is already waiting for Admin approval."

        new_request = TrekChangeRequest(
            trek_id=trek.id,
            staff_id=staff.id,
            change_type="status",
            requested_value=status,
            status="Pending"
        )

        db.session.add(new_request)
        db.session.commit()

        return redirect("/my_treks")

    return render_template(
        "Staff/update_status.html",
        trek=trek
    )

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

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    trek = Trekking_table.query.get_or_404(trek_id)

    if trek.staff_id != staff.id:
        return "You cannot update this trek."

    if request.method == "POST":

        try:
            new_slots = int(request.form["slots"])
        except:
            return "Please enter a valid number of slots."

        if new_slots <= 0:
            return "Available slots must be greater than 0."

        booked_count = Booking.query.filter_by(
            trekking_id=trek.id,
            booking_status="Booked"
        ).count()

        if new_slots < booked_count:
            return "Available slots cannot be less than booked participants."

        existing_request = TrekChangeRequest.query.filter_by(
            trek_id=trek.id,
            change_type="slots",
            status="Pending"
        ).first()

        if existing_request:
            return "A slots change request is already waiting for Admin approval."

        new_request = TrekChangeRequest(
            trek_id=trek.id,
            staff_id=staff.id,
            change_type="slots",
            requested_value=str(new_slots),
            status="Pending"
        )

        db.session.add(new_request)
        db.session.commit()

        return redirect("/my_treks")

    return render_template(
        "Staff/update_slots.html",
        trek=trek
    )

@app.route("/request_staff_status", methods=["POST"])
def request_staff_status():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    staff.status = "Pending"

    db.session.commit()

    return redirect("/staff_dashboard")

@app.route("/staff_search", methods=["GET", "POST"])
def staff_search():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "staff":
        return "Access Denied"

    staff = Staff.query.filter_by(
        name=session["username"]
    ).first()

    if not staff:
        return "Staff record not found."

    treks = Trekking_table.query.filter_by(
        staff_id=staff.id
    ).all()

    if request.method == "POST":

        keyword = request.form["search"]

        treks = Trekking_table.query.filter(
            Trekking_table.staff_id == staff.id,
            (Trekking_table.name.contains(keyword)) |
            (Trekking_table.location.contains(keyword)) |
            (Trekking_table.difficulty.contains(keyword)) |
            (Trekking_table.status.contains(keyword))
        ).all()

    return render_template(
        "Staff/search_my_trek.html",
        treks=treks
    )

# User

@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "user":
        return "Access Denied"

    return render_template("User/user_dashboard.html")

@app.route("/edit_profile/<int:user_id>", methods=["GET", "POST"])
def edit_profile(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "user":
        return "Access Denied"

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
    if session.get("role") != "user":
        return "Access Denied"

    treks = Trekking_table.query.all()
    return render_template("User/browse_treks.html", treks=treks)

@app.route("/trek_details/<int:trek_id>")
def trek_details(trek_id):

    if "user_id" not in session:
        return redirect("/login")
    if session.get("role") != "user":
        return "Access Denied"
    
    trek = Trekking_table.query.get_or_404(trek_id)

    return render_template("User/view_trek.html",trek=trek) 

@app.route("/my_bookings")
def my_bookings():

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "user":
        return "Access Denied"


    bookings = Booking.query.filter_by(user_id=session["user_id"]).all()

    return render_template("User/my_bookings.html", bookings=bookings)

@app.route("/search_treks", methods=["GET", "POST"])
def search_treks():

    if "user_id" not in session:
        return redirect("/login")
    
    if session.get("role") != "user":
        return "Access Denied"

    treks = Trekking_table.query.all()

    if request.method == "POST":

        search = request.form["search"]

        treks = Trekking_table.query.filter(
            (Trekking_table.name.contains(search)) |
            (Trekking_table.location.contains(search)) |
            (Trekking_table.difficulty.contains(search))
        ).all()

    return render_template("User/search_treks.html",treks=treks)

@app.route("/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):

    if "user_id" not in session:
        return redirect("/login")

    if session.get("role") != "user":
        return "Access Denied"

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session["user_id"]:
        return "Access Denied"

    if booking.booking_status == "Cancelled":
        return "This booking is already cancelled."

    trek = Trekking_table.query.get(booking.trekking_id)

    if trek:
        trek.available_slots += 1

    booking.booking_status = "Cancelled"

    db.session.commit()

    return redirect("/my_bookings")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        exist_admin = User.query.filter_by(username="admin").first()
        if not exist_admin:
            admin_new = User(username = "admin", email = "admin@gmail.com", password= "admin123", role="admin")
            db.session.add(admin_new)
            db.session.commit()
    app.run(debug=True) 
