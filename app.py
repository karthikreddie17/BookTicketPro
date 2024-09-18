from flask import Flask, request, redirect, url_for, render_template as rt
from flask_security import Security, SQLAlchemyUserDatastore, login_required, login_user,current_user
from flask_security.utils import hash_password, verify_password
from model import *
import os
from flask_restful import Api
from api import *
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from celery_worker import make_celery
from datetime import timedelta
from Email import send_email
from datetime import datetime
import calendar,time
from functools import wraps
from flask import flash, send_file
from io import StringIO
import csv
from instances import cache

app = Flask(__name__)
current_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(current_dir, "mad2data.sqlite3")
app.config['SECRET_KEY'] = 'supersecret'
app.config['SECURITY_PASSWORD_SALT'] = 'salt'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY']='SECRETKEYFORENCRYPTION'
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    result_backend='redis://localhost:6379'
)

app.jinja_options = app.jinja_options.copy()
app.jinja_options['variable_start_string'] = '[[ '
app.jinja_options['variable_end_string'] = ' ]]'


app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_HOST"] = "localhost"
app.config["CACHE_REDIS_PORT"] = 6379
app.config["CACHE_REDIS_DB"] = 3
app.config["CACHE_REDIS_URL"] = "redis://localhost:6379/1"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300


db.init_app(app)
jwt= JWTManager(app)

celery=make_celery(app)
cache.init_app(app)


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
gived_roles = False  # Flag to track if roles have been initialized



api = Api(app)
api.add_resource(SectionResource, '/api/sections', '/api/sections/<section_id>')
api.add_resource(BookResource, '/api/sections/<int:section_id>/books','/api/sections/<int:section_id>/books/<int:book_id>')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('admin'):
            flash('You do not have permission to access this page.', 'danger')
            
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_role('user'):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def giving_roles():
    global gived_roles
    if not gived_roles:
        if not Role.query.filter_by(name='user').first():
            user_role = Role(name='user', description='Basic User Role')
            db.session.add(user_role)
        if not Role.query.filter_by(name='admin').first():
            admin_role = Role(name='admin', description='Admin Role')
            db.session.add(admin_role)
        db.session.commit()
        gived_roles = True  # Set flag to True after roles are initialized
    if not User.query.filter_by(email='admin@gmail.com').first():
        admin_user = user_datastore.create_user(
            username='admin',
            email='admin@gmail.com',
            password=hash_password('admin@123'),
            user_type='admin',
            active=True
        )
        admin_role = Role.query.filter_by(name='admin').first()
        admin_user.roles.append(admin_role)
        db.session.commit()

# Call giving_roles when the application starts
with app.app_context():
    db.create_all()
    giving_roles()

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_data = User.query.filter_by(email=email).first()
        if user_data and verify_password(password, user_data.password):
            login_user(user_data)
            global token
            token = create_access_token(identity = user_data.email)
            user_data.API_token = token
            user_data.last_login = datetime.now()
            db.session.commit()
            if user_data.user_type == 'user':
                return jsonify({'redirect': url_for('user_dashboard'), 'token': token})
            elif user_data.user_type == 'admin':
                return jsonify({'redirect': url_for('librarian_dashboard'), 'token': token})

        return rt('home.html', message="Wrong email or password")
    return rt('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_type = request.form['type']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        if not User.query.filter_by(email=email).first():
            new_user = user_datastore.create_user(
                username=username,
                email=email,
                password=hash_password(password),
                user_type=user_type
            )
            role = Role.query.filter_by(name='admin' if user_type == 'admin' else 'user').first()
            if role:
                new_user.roles.append(role)
            db.session.commit()
            return redirect(url_for('home'))
    return rt('signup.html')

@app.route('/user_dashboard', methods=['GET'])
@login_required
# @jwt_required()
@user_required
def user_dashboard():
    # user_id = get_jwt_identity()
    return rt('userDashboard.html')

@app.route('/librarian_dashboard', methods=['GET'])
@login_required
@admin_required
def librarian_dashboard():
    
    return rt('librarianDashboard.html')

# @app.route('/add_section',methods=['GET','POST'])
# @login_required
# def add_section():
#     if request.method == 'GET':
#         return rt('add_section_form.html')
#     return rt('')



@app.route('/add_section', methods=['GET', 'POST'])
@admin_required
@login_required
def add_section():
    section_id = request.args.get('sectionId')
    if request.method == 'GET':
        if section_id:
            section = Section.query.filter_by(id=section_id).first()
            if section:
                return rt('add_section_form.html', section=section)
            return "Section not found", 404
        return rt('add_section_form.html')
    return rt('')


@app.route('/add_book', methods=['GET'])
@login_required
@admin_required
def add_book():
    section_id = request.args.get('sectionId')
    book_id = request.args.get('bookId', None)  # Optional, for updates

    if not section_id:
        return "Section ID is required", 400

    # Debug output to console
    print(f"Section ID: {section_id}")
    if book_id:
        print(f"Book ID: {book_id}")
        return rt('add_book.html', sectionId=section_id, bookId=book_id)

    return rt('add_book.html', sectionId=section_id)

# @app.route('/add_book', methods=['GET'])
# @login_required
# def add_book():
#     section_id = request.args.get('sectionId')
#     print(f"Section ID: {section_id}") 

#     if not section_id:
#         return "Section ID is required", 400

#     return rt('add_book.html', sectionId=section_id)




@app.route('/api/books/<int:bookId>/request', methods=['GET','POST'])
# @login_required
@jwt_required()
def request_book(bookId):
    user_id = get_jwt_identity()  # Retrieve user ID from JWT token
    with Session(db.engine) as session:
        book_status = session.query(BookStatus).filter_by(book_id=bookId, user_id=user_id).first()
        numberofallocated_books = BookStatus.query.filter_by(user_id=user_id, is_allocated=1).count()
        number_of_requested_books  = BookStatus.query.filter_by(user_id=user_id, is_requested=1).count()
        if numberofallocated_books + number_of_requested_books  >= 5:
            return jsonify({'message': 'A User can only request 5 books at a time'}), 400
        # Check if the book is already allocated or requested

        if book_status:
            if book_status.is_allocated:
                return jsonify({"message": "Book is already allocated"}), 409
            elif book_status.is_requested:
                return jsonify({
                    "message": "Book is already requested",
                    "date_of_issue": book_status.date_of_issue.strftime('%Y-%m-%d') if book_status.date_of_issue else 'N/A',
                    "return_date": book_status.return_date.strftime('%Y-%m-%d') if book_status.return_date else 'N/A'
                }), 409
            else:
                book_status.is_requested = 1
                book_status.date_of_issue = datetime.now()
                book_status.return_date = datetime.now() + timedelta(days=7)
                book_status.status="requested"
            
        else:
            # If not requested or allocated, set as requested and assign dates
            current_date = datetime.now()
            return_date = current_date + timedelta(days=7)  # Setting a return date 7 days from now
            book_status = BookStatus(
                book_id=bookId,
                user_id=user_id,
                is_requested=1,
                is_allocated=0,
                date_of_issue=current_date,
                return_date=return_date,
                status="requested"
            )
            session.add(book_status)
        
        session.commit()
        return jsonify({
            "message": "Request submitted successfully",
            "request_id": book_status.id,
            "date_of_issue": book_status.date_of_issue.strftime('%Y-%m-%d'),
            "return_date": book_status.return_date.strftime('%Y-%m-%d'),
            "status" : book_status.status,
            "book": {
            "id": bookId,
            "requested": book_status.is_requested,
            "allocated": book_status.is_allocated,
            "status": book_status.status
        }
        }), 200

@app.route('/requests', methods=['GET','POST'])
@login_required
@admin_required
def requests():
    return rt('requests.html')

@app.route('/requests_user', methods=['GET','POST'])
@login_required
@user_required
def requests_user():
    return rt('requests_user.html')

@app.route('/api/requests', methods=['GET'])    
@jwt_required()
def get_requested_books():
    with Session(db.engine) as session:
        user_id=get_jwt_identity()
        # Fetch books where they are requested but not allocated
       
        requested_books = session.query(BookStatus).filter_by(is_requested=1, is_allocated=0).all()
        books_list = [
            {
                "book_id": book.book_id,
                "user_id": book.user_id,
                # "date_of_issue": book.date_of_issue.strftime('%Y-%m-%d') if book.date_of_issue else 'N/A',
                # "return_date": book.return_date.strftime('%Y-%m-%d') if book.return_date else 'N/A',
                "status": "Requested"
            } for book in requested_books
        ]
        return jsonify(books_list)


@app.route('/api/grant_book', methods=['GET','POST'])
@login_required
@jwt_required()
def grant_book():
    user_id = request.json.get('user_id')
    book_id= request.json.get('book_id')
    print(user_id,book_id)
    if not user_id:
        return jsonify({"message": "User ID is required"}), 400

    with Session(db.engine) as session:
        # Update the BookStatus
        book_status = session.query(BookStatus).filter_by(book_id=book_id,is_requested=1,is_allocated=0).first()
        if not book_status or book_status.is_allocated:
            return jsonify({"message": "Book is already allocated or not found"}), 404
        
        book_status.is_allocated = 1
        book_status.is_requested = 0
        book_status.status="allocated"
        session.commit()

        # Add or update BookIssued entry
        book_issued = session.query(BookIssued).filter_by(book_id=book_id, user_id=user_id).first()
        if not book_issued:
            book_issued = BookIssued(
                book_id=book_id,
                user_id=user_id,
                date_of_issue=datetime.now(),
                return_date=datetime.now() + timedelta(days=7),
                returned=0  # Assume '0' means not yet returned
            )
            session.add(book_issued)
        else:
            book_issued.date_of_issue = datetime.now()
            book_issued.return_date = datetime.now() + timedelta(days=7)
            book_issued.returned = 0

        session.commit()
        return jsonify({"message": "Book granted successfully"}), 200
    
@app.route('/api/reject_book', methods=['POST'])
@jwt_required()
def reject_book():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    if not user_id or not book_id:
        return jsonify({"message": "Both user ID and book ID are required"}), 400

    with Session(db.engine) as session:
        # Update the BookStatus to mark as not requested and not allocated
        book_status = session.query(BookStatus).filter_by(book_id=book_id, user_id=user_id,is_requested=1,is_allocated=0).first()
        if not book_status:
            return jsonify({"message": "No such book request found"}), 404

        book_status.is_requested = 0
        book_status.is_allocated = 0
        book_status.date_of_issue= None
        book_status.return_date= None
        book_status.status="request"
        session.commit()

        return jsonify({"message": "Book request successfully rejected"}), 200


@app.route('/allocated', methods=['GET','POST'])
@admin_required
@login_required
def allocated():
    return rt('allocated.html')

@app.route('/api/allocated_books', methods=['GET','POST'])
@jwt_required()
def get_allocated_books():
    with Session(db.engine) as session:
        user_id = get_jwt_identity()
        # Query the BookStatus table to find all entries where is_allocated is True
        allocated_books = session.query(BookStatus).filter_by(is_allocated=1).all()
        book_ids = [book.book_id for book in allocated_books]
        if book_ids:
            books_details = session.query(Book).filter(Book.id.in_(book_ids)).all()
            books_detail_map = {book.id: book for book in books_details}
        else:
            books_detail_map = {}
        books_list = [
            {
                "book_id": book.book_id,
                "title": books_detail_map.get(book.book_id).title if book.book_id in books_detail_map else "Unknown",
                "content": books_detail_map.get(book.book_id).content if book.book_id in books_detail_map else "No Content",
                "authors": books_detail_map.get(book.book_id).authors if book.book_id in books_detail_map else "Unknown Authors",
                "rating": books_detail_map.get(book.book_id).rating if book.book_id in books_detail_map else "No Rating",
                "user_id": book.user_id,
                "date_of_issue": book.date_of_issue.strftime('%Y-%m-%d') if book.date_of_issue else 'N/A',
                "return_date": book.return_date.strftime('%Y-%m-%d') if book.return_date else 'N/A',
                "status": "allocated"
            } for book in allocated_books
        ]
        return jsonify(books_list)

@app.route('/api/deallocate_book', methods=['GET','POST'])
@jwt_required()
def deallocate_book():
    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({"message": "Book ID is required"}), 400

    with Session(db.engine) as session:
        book_status = session.query(BookStatus).filter_by(book_id=book_id, is_allocated=1).first()
        if not book_status:
            return jsonify({"message": "No such allocated book found"}), 404

        book_status.is_allocated = 0
        book_status.date_of_issue= None
        book_status.return_date= None
        book_status.status="request"
        
        book_issued_entry = session.query(BookIssued).filter_by(book_id=book_id).first()
        if book_issued_entry:
            session.delete(book_issued_entry)

        session.commit()

        return jsonify({"message": "Book successfully deallocated"}), 200




@app.route('/api/initialize_book_status', methods=['POST'])
@user_required
@jwt_required()
def initialize_book_status():
    user_id = get_jwt_identity()
    with Session(db.engine) as session:
        books = Book.query.all()  # Assuming you want to initialize for all books
        for book in books:
            if not BookStatus.query.filter_by(book_id=book.id, user_id=user_id).first():
                new_status = BookStatus(
                    book_id=book.id,
                    user_id=user_id,
                    is_requested=0,
                    is_allocated=0,
                    status='request'
                )
                session.add(new_status)
        session.commit()
    return jsonify({"message": "All book statuses initialized for the user."})



@app.route('/allocated_user', methods=['GET','POST'])
@login_required
@user_required
def allocated_user():
    return rt('allocated_user.html')

@app.route('/api/allocated_books_user', methods=['GET','POST'])
@jwt_required()
@cache.cached(timeout=500)
def get_allocated_books_user():
    with Session(db.engine) as session:
        user_id = get_jwt_identity()
        # Query the BookStatus table to find all entries where is_allocated is True
        # allocated_books = session.query(BookIssued).filter_by(returned=0).all()
        allocated_books = session.query(BookIssued) \
            .join(Book, BookIssued.book_id == Book.id) \
            .filter(BookIssued.returned == 0, BookIssued.user_id == user_id) \
            .all()
        books_list = [
            {
                "book_id": book.book_id,
                "title": book.book.title,
                "content": book.book.content,
                "authors": book.book.authors,
                "user_id": book.user_id,
                "date_of_issue": book.date_of_issue.strftime('%Y-%m-%d') if book.date_of_issue else 'N/A',
                "return_date": book.return_date.strftime('%Y-%m-%d') if book.return_date else 'N/A',
                "status": "Allocated"
            } for book in allocated_books
        ]
        return jsonify(books_list)
     
@app.route('/api/rate_and_feedback_book', methods=['POST'])
@jwt_required()
def rate_and_feedback_book():
    data = request.get_json()
    book_id = data.get('book_id')
    rating = data.get('rating')
    feedback = data.get('feedback')

    if not book_id or rating is None or feedback is None:
        return jsonify({"message": "Book ID, rating, and feedback are required"}), 400

    with Session(db.engine) as session:
        book_issued = session.query(BookIssued).filter_by(book_id=book_id).first()
        if not book_issued:
            return jsonify({"message": "Book not found"}), 404

        book_issued.rating = rating
        book_issued.feedback = feedback
        session.commit()

        return jsonify({"message": "Feedback and rating updated successfully"}), 200

@app.route('/api/return_book', methods=['GET','POST'])
@jwt_required()
def return_book():
    data = request.get_json()
    book_id = data.get('book_id')

    if not book_id:
        return jsonify({"message": "Book ID is required"}), 400

    with Session(db.engine) as session:
        book_status = session.query(BookIssued).filter_by(book_id=book_id).first()
        if not book_status:
            return jsonify({"message": "No such book found"}), 404

        book_status.returned = 1
        book_status.date_of_issue= datetime.now() 
        book_status.return_date= datetime.now() + timedelta(days=7)

        book_status = session.query(BookStatus).filter_by(book_id=book_id).first()
        if book_status:
            book_status.status = 'returned'
        session.commit()

        return jsonify({"message": "Book successfully returned"}), 200

#graphs in admin

@app.route('/api/books_per_section')
@login_required
def books_per_section():
    results = db.session.query(
        Section.name, db.func.count(Book.id).label('book_count')
    ).join(Book, Section.id == Book.section_id).group_by(Section.name).all()

    data = {result[0]: result[1] for result in results}
    return jsonify(data)

@app.route('/api/book_ratings')
@login_required
def book_ratings():
    results = db.session.query(
        Book.title, db.func.avg(BookIssued.rating).label('average_rating')
    ).join(BookIssued, Book.id == BookIssued.book_id).group_by(Book.title).all()

    data = {result[0]: float(result[1]) for result in results if result[1] is not None}
    return jsonify(data)


@app.route('/api/most_requested_books')
@login_required
def most_requested_books():
    results = db.session.query(
        Book.title, db.func.count(BookIssued.id).label('request_count')
    ).join(BookIssued, Book.id == BookIssued.book_id).group_by(Book.title).order_by(db.desc('request_count')).limit(5).all()

    data = {result[0]: result[1] for result in results}
    return jsonify(data)


@app.route('/stats',methods=['GET','POST'])
@admin_required
@login_required
def stats():
    return rt('stats.html')

@app.route('/stats_user',methods=['GET','POST'])
@login_required
@user_required
def stats_user():
    return rt('stats_user.html')



from datetime import datetime, timedelta
import pytz


###############################################################################################3

from Email import send_email

@celery.task
def daily_user_reminder(): # Sending daily reminders to users who haven't logged in for a day
    yesterday = datetime.now(pytz.timezone('Asia/Kolkata')) - timedelta(days=1)
    users_to_remind = User.query.filter(User.last_login < yesterday).all()
    for user in users_to_remind:
        msg = rt('reminder_daily.html', user_name= user.username)
        send_email(to_address=user.email, subject= "Website reminder", message=msg)


@celery.task
def generate_monthly_report():  # Generate and send monthly reports to all users.
    users = User.query.all()
    for user in users:
        allocated_books_count = BookIssued.query.filter_by(user_id=user.email).count()
        # print(allocated_books_count) 
        distinct_sections_count = Book.query.join(BookIssued).filter(BookIssued.user_id == user.email).distinct(Book.section_id).count()
        returned_books_count = BookIssued.query.filter_by(user_id=user.email, returned=1).count()
        # avg_rating = db.session.query(func.avg(BookIssued.rating)).filter(BookIssued.user_id == user.email).scalar()
        msg = rt("monthly_report.html", user=user.username, books_alloc=allocated_books_count,sections_explored=distinct_sections_count,books_returned=returned_books_count,
            # average_rating=avg_rating
        )
        send_email(to_address=user.email, subject="Montly User Report", message=msg)

#csv data async job
@celery.task(name='app.generate_csv')
def generate_csv(user_email):
    rows = []

    # Perform a join between Book and BookIssued tables
    book_issued_data = db.session.query(
        BookIssued.id,
        BookIssued.user_id,
        BookIssued.book_id,
        Book.title,
        Book.content,
        # rating feedback kuda peptochu 
        Book.authors,
        BookIssued.date_of_issue,
        BookIssued.return_date
    ).join(Book, Book.id == BookIssued.book_id).all()

    for record in book_issued_data:
        rows.append([
            record.id,
            record.user_id,
            record.book_id,
            record.title,
            record.content,
            record.authors,
            record.date_of_issue,
            record.return_date
        ])

    fields = ['Id','User Id','Book Id', 'Title', 'Content', 'Author(s)', 'Date Issued', 'Return Date']

    output_path = os.path.join("static", "books_report.csv")

    with open(output_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(rows)

    # Send an email to the librarian notifying them that the CSV is ready
    send_email(
        to_address=user_email,
        subject="CSV Export Completed",
        message="The CSV export has been completed. Please download the file from the admin dashboard.",
    )
    
    return "CSV file generated."

@app.route("/trigger-csv-export", methods=["POST"])
def trigger_csv_export():
    user_email = request.json.get('email')  # Expecting the librarian's email in the request body 
    task = generate_csv.delay(user_email)
    return jsonify({
        "Task_ID": task.id,
        "Task_State": task.state,
        "Task_Result": task.result
    }), 202

@app.route("/status/<id>")
def check_status(id):
    res = celery.AsyncResult(id)
    return jsonify({
        "Task_ID": res.id,
        "Task_State": res.state,
        "Task_Result": res.result
    })

@app.route("/download-csv")
def download_file():
    return send_file("static/books_report.csv", as_attachment=True, download_name='books_report.csv')




celery.conf.beat_schedule = {

            'task_daily_reminder': {
            'task': 'app.daily_user_reminder',
            'schedule': timedelta(seconds=30),  #run daily
            },

            'task_monthly_report': {
                'task': 'app.generate_monthly_report',
                'schedule': timedelta(seconds=30),  # run monthly
            },
            'task_generate_csv': {
                'task': 'app.generate_csv',
                'schedule': timedelta(seconds=30),  # Example: Run weekly
                'args': ['librarian@mkr.com']  # Pass the librarian's email
            }
                            
    }





if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
