from datetime import datetime
import re
from flask import Flask, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, join_room, send, emit

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://official_wings_db_1q3g_user:usySpzm5qAApcUNGZGMLdSltem2IpXyb@dpg-cr4p7j52ng1s73e4vavg-a.frankfurt-postgres.render.com/official_wings_db_1q3g'
socketio = SocketIO(app)
db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = 'userdetails'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(200), unique=True,nullable=False)
    password = db.Column(db.String, nullable=False)


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('Task', foreign_keys=[sender_id], backref=db.backref('sent_messages', lazy=True))
    receiver = db.relationship('Task', foreign_keys=[receiver_id], backref=db.backref('received_messages', lazy=True))


class UserData(db.Model):
    __tablename__ = 'userdata'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_auth_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)
    name = db.Column(db.String(255))
    email = db.Column(db.String(200))
    gender = db.Column(db.String(50))
    hobbies = db.Column(db.ARRAY(db.String))
    phone_number = db.Column(db.String(50))
    age = db.Column(db.String(10))
    bio = db.Column(db.Text)
    
    user = db.relationship('Task', backref=db.backref('user_data', lazy=True))

class UserImages(db.Model):
    __tablename__ = 'userImage'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_auth_id = db.Column(db.Integer, db.ForeignKey('userdetails.id'), nullable=False)
    email = db.Column(db.String(200))  # Ensure this column exists
    imageString = db.Column(db.String())
    user = db.relationship('Task', backref=db.backref('user_image', lazy=True))

with app.app_context():
    db.create_all()

# METHOD TO GET AUTHENTICATED USERS LIST
@app.get("/users")
def home():
    tasks = Task.query.all()
    task_list = [
        {'id': task.id, 'email': task.email, 'password': task.password} for task in tasks
    ]
    return jsonify({"user_details": task_list})

# POST USER CREDENTIALS TO DATABASE
@app.route('/users', methods=['POST'])
def postData():
    try:
        data = request.get_json()
        new_email = data.get('email')
        new_password = data.get('password')

        if not new_email or not new_password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Validate email format
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, new_email):
            return jsonify({'message': 'Invalid email format'}), 400

        # Check if the email already exists
        existing_user = Task.query.filter_by(email=new_email).first()
        if existing_user:
            return jsonify({'message': 'Email already exists'}), 400

        # Create new user
        newUserDetails = Task(email=new_email, password=new_password)
        db.session.add(newUserDetails)
        db.session.commit()
        return jsonify({'message': "New User added"}), 201

    except Exception as e:
        print(e)
        return jsonify({'error': 'Internal Server Error'}), 500



# POSTING USER DATA TO DATABASE
@app.route('/userData', methods=['POST'])
def postUserData():
    try:  # Added closing parenthesis here
        data = request.get_json()
        newEmail = data['email']
        user = Task.query.filter_by(email=newEmail).first()

        if not user:
            return jsonify({'error': "No User registered with this mail"}), 400

        user_auth_id = user.id
        name = data['name']
        gender = data['gender']
        hobbies = data['hobbies']
        phone_number = data['phone_number']
        age = data['age']
        bio = data['bio']
      

        # Check if user details already exist
        userDetails = UserData.query.filter_by(user_auth_id=user_auth_id).first()

        if userDetails:
            # Update existing user details
            userDetails.name = name
            userDetails.email = newEmail
            userDetails.gender = gender
            userDetails.hobbies = hobbies
            userDetails.phone_number = phone_number
            userDetails.age = age
            userDetails.bio = bio
         
            message = "Updated user details"
        else:
            # Add new user details
            userDetails = UserData(
                user_auth_id=user_auth_id,
                name=name,
                email=newEmail,
                gender=gender,
                hobbies=hobbies,
                phone_number=phone_number,
                age=age,
                bio=bio
            )
            db.session.add(userDetails)
            message = "Added user details"

        db.session.commit()
        return jsonify({'message': message}), 201

    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        newEmail = data['email']
        image_string = data.get('imageString')

        # Ensure that email and imageString are provided
        if not newEmail or not image_string:
            return jsonify({"error": "Email and imageString are required"}), 400

        # Get user by email
        user = Task.query.filter_by(email=newEmail).first()

        if not user:
            return jsonify({'error': "No User registered with this mail"}), 400

        user_auth_id = user.id

        # Check if an image already exists for this user
        user_image = UserImages.query.filter_by(user_auth_id=user_auth_id).first()

        if user_image:
            # Update existing image
            user_image.imageString = image_string
            message = "Updated user image"
        else:
            # Add new image
            user_image = UserImages(
                user_auth_id=user_auth_id,
                email=newEmail,
                imageString=image_string
            )
            db.session.add(user_image)
            message = "Added new user image"

        db.session.commit()
        return jsonify({"message": message}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get_image/<int:user_auth_id>', methods=['GET'])
def get_image(user_auth_id):
    # Query the database for a single record matching the user_auth_id
    user_image = UserImages.query.filter_by(user_auth_id=user_auth_id).first()

    if user_image:
        # Return the image as an object
        return jsonify({
            "id": user_image.id,
            "email":user_image.email,
            "user_auth_id": user_image.user_auth_id,
            "imageString": user_image.imageString
        }), 200
    else:
        return jsonify({"error": "No image found for the given user_auth_id"}), 404


    
@app.route('/userData', methods=['GET'])
def getUserData():
    try:
        # Query all user details
        userDetailsList = UserData.query.all()
        
        # Prepare the response data
        users = []
        for userDetails in userDetailsList:
            user = {
                'id': userDetails.user_auth_id,
                'name': userDetails.name,
                'email': userDetails.email,
                'gender': userDetails.gender,
                'hobbies': userDetails.hobbies,
                'phone_number': userDetails.phone_number,
                'age': userDetails.age,
                'bio': userDetails.bio
            }
            users.append(user)
        
        return jsonify({'users': users}), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500



# USER SIGNIN METHOD
@app.route('/sign-in', methods=['POST'])
def sign_in():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = Task.query.filter_by(email=email).first()

        if user:
            if password == user.password:  # Compare passwords directly
                return jsonify({'message': 'Sign in successful'}), 200
            else:
                return jsonify({'message': 'Invalid credentials'}), 401
        else:
            return jsonify({'message': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500



@app.route('/send_message', methods=['POST'])
def send_message():
    sender_id = request.form.get('sender_id')
    receiver_id = request.form.get('receiver_id')
    message = request.form.get('message')

    # Check if any of the fields are missing
    if not sender_id or not receiver_id or not message:
        return jsonify({'error': 'Missing data'}), 400

    # Store the message in the database
    new_message = Message(sender_id=sender_id, receiver_id=receiver_id, message=message)
    db.session.add(new_message)
    db.session.commit()

    # Emit the message to the receiver's room
    socketio.emit('receive_message', {'sender_id': sender_id, 'receiver_id': receiver_id, 'message': message}, room=receiver_id)
    return jsonify({'status': 'Message sent'})

@socketio.on('send_message')
def handle_message(data):
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    message = data['message']

    # Store the message in the database
    new_message = Message(sender_id=sender_id, receiver_id=receiver_id, message=message)
    db.session.add(new_message)
    db.session.commit()

    emit('receive_message', {'sender_id': sender_id, 'receiver_id': receiver_id, 'message': message}, room=receiver_id)

@socketio.on('join')
def on_join(data):
    user_id = data['user_id']
    join_room(user_id)
    emit('status', {'msg': f'User {user_id} has entered the room.'}, room=user_id)
    
@app.route('/get_chats', methods=['GET'])
def get_chats():
    email1 = request.args.get('email1')
    email2 = request.args.get('email2')

    if not email1 or not email2:
        return jsonify({'error': 'Missing email addresses'}), 400

    # Retrieve user IDs based on the provided emails
    user1 = Task.query.filter_by(email=email1).first()
    user2 = Task.query.filter_by(email=email2).first()

    if not user1 or not user2:
        return jsonify({'error': 'One or both users not found'}), 404

    # Fetch the chat history between the two users
    messages = Message.query.filter(
        ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
        ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
    ).order_by(Message.timestamp).all()

    # Prepare the chat history for response, adding sender and receiver emails
    chat_history = [
        {
            'sender_id': msg.sender_id,
            'sender_email': user1.email if msg.sender_id == user1.id else user2.email,
            'receiver_id': msg.receiver_id,
            'receiver_email': user2.email if msg.receiver_id == user2.id else user1.email,
            'message': msg.message,
            'timestamp': msg.timestamp
        }
        for msg in messages
    ]

    return jsonify(chat_history)


    

# if __name__ == '__main__':
#     app.run()
