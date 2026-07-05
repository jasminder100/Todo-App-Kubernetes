import os
from flask import Flask, request, jsonify # render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

# Build MySQL connection string from .env
DB_USER     = os.getenv('DB_USER', 'user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST     = os.getenv('DB_HOST', 'localhost')
DB_PORT     = os.getenv('DB_PORT', '3306')
DB_NAME     = os.getenv('DB_NAME', 'todo_db')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST).replace(tzinfo=None)

# Model matches exactly the table you already created
class Todo(db.Model):
    __tablename__ = 'todos'
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default='Pending')
    created_at  = db.Column(db.DateTime, default=now_ist)
    updated_at  = db.Column(db.DateTime, default=now_ist, onupdate=now_ist)

#@app.route('/')
#def index():
 #   return render_template('index.html')

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.order_by(Todo.created_at.asc()).all()
    return jsonify([{
        'id':          t.id,
        'title':       t.title,
        'description': t.description,
        'status':      t.status,
        'created_at':  t.created_at.isoformat() if t.created_at else None,
        'updated_at':  t.updated_at.isoformat() if t.updated_at else None
    } for t in todos])

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.json
    if not data or not data.get('title', '').strip():
        return jsonify({'error': 'Title is required'}), 400
    todo = Todo(
        title=data['title'].strip(),
        description=data.get('description', '').strip()
    )
    db.session.add(todo)
    db.session.commit()
    return jsonify({'id': todo.id, 'message': 'Created'}), 201

@app.route('/todos/<int:id>', methods=['PUT'])
def update_todo(id):
    todo = Todo.query.get_or_404(id)
    data = request.json
    if 'title' in data:
        todo.title = data['title'].strip()
    if 'description' in data:
        todo.description = data['description'].strip()
    if 'status' in data:
        todo.status = data['status']
    todo.updated_at = now_ist()
    db.session.commit()
    return jsonify({'message': 'Updated'})

@app.route('/todos/<int:id>', methods=['DELETE'])
def delete_todo(id):
    todo = Todo.query.get_or_404(id)
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

if __name__ == '__main__':
    app.run(debug=True)