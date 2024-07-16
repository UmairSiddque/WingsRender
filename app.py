from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://wings_render_database_user:LEPEFJsnwID4c5kMiRYjxcAEVTqYu1jj@dpg-cqamrv0gph6c73f6qbsg-a.oregon-postgres.render.com/wings_render_database'

db = SQLAlchemy(app)

class Task(db.Model):
    __tablename__ = 'userdetails'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String, nullable=False)

with app.app_context():
    db.create_all()

@app.get("/users")
def home():
    tasks = Task.query.all()
    task_list = [
        {'id': task.id, 'email': task.email, 'password': task.password} for task in tasks
    ]
    return jsonify({"user_details": task_list})

@app.route('/users', methods=['POST'])
def postData():
    data = request.get_json()  # Call the method to get the JSON data
    newUserDetails = Task(email=data['email'], password=data['password'])
    db.session.add(newUserDetails)
    db.session.commit()  # Don't forget to commit the transaction
    return jsonify({'message': "New User added"})

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
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500
    

# if __name__ == '__main__':
#     app.run()
