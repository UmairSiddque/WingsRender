from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:umair123@localhost:5432/WingsDatabase'

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


# if __name__ == '__main__':
#     app.run()
