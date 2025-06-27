import hashlib
import jwt
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta

from database import db, Voter
from blockchain import Blockchain

app = Flask(__name__)
# Configure CORS to allow requests from the frontend
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "x-access-token"]
    }
})

# --- App Configuration ---
app.config['SECRET_KEY'] = 'your_super_secret_key_change_it_later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voters.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- Blockchain Instance ---
bc = Blockchain()

# --- Admin Configuration ---
ADMIN_ID = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('admin_password'.encode()).hexdigest()

# --- Helper Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- JWT Decorators ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = Voter.query.filter_by(voter_id=data['voter_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            if not data.get('admin'):
                return jsonify({'message': 'Admin privileges required!'}), 403
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

# --- API Routes ---
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('voterId') or not data.get('password'):
        return jsonify({'message': 'Missing data'}), 400

    if Voter.query.filter_by(voter_id=data['voterId']).first():
        return jsonify({'message': 'Voter ID already registered'}), 409

    hashed_password = hash_password(data['password'])
    new_voter = Voter(name=data['name'], voter_id=data['voterId'], password_hash=hashed_password)
    db.session.add(new_voter)
    db.session.commit()
    return jsonify({'message': 'New voter registered!'}), 201

@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if not auth or not auth.get('voterId') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401

    voter = Voter.query.filter_by(voter_id=auth['voterId']).first()
    if not voter or not voter.password_hash == hash_password(auth['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'voter_id': voter.voter_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})

@app.route('/admin-login', methods=['POST'])
def admin_login():
    auth = request.get_json()
    if not auth or not auth.get('adminId') or not auth.get('password'):
        return jsonify({'message': 'Could not verify'}), 401
    
    if auth['adminId'] == ADMIN_ID and hash_password(auth['password']) == ADMIN_PASSWORD_HASH:
        token = jwt.encode({
            'admin': True,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token})

    return jsonify({'message': 'Invalid admin credentials'}), 401

@app.route('/vote', methods=['POST'])
@token_required
def cast_vote(current_user):
    if current_user.has_voted:
        return jsonify({'message': 'You have already voted!'}), 403

    data = request.get_json()
    candidate_id = data.get('candidateId')
    if not candidate_id:
        return jsonify({'message': 'Candidate ID is missing!'}), 400

    voter_id_hash = hash_password(current_user.voter_id)
    bc.new_vote(voter_id_hash=voter_id_hash, candidate_id=candidate_id)
    
    current_user.has_voted = True
    db.session.commit()

    # Automatically mine a new block with this vote
    last_block = bc.last_block
    last_proof = last_block['proof']
    proof = last_proof + 1
    new_block = bc.new_block(proof)

    return jsonify({
        'message': 'Vote cast successfully and added to blockchain!',
        'block_index': new_block['index']
    }), 200

@app.route('/admin/results', methods=['GET'])
@admin_required
def get_results():
    # Process the blockchain to get vote counts
    vote_counts = {}
    total_votes = 0
    
    # Count votes from all blocks
    for block in bc.chain:
        for vote in block.get('votes', []):
            candidate_id = vote['candidate_id']
            vote_counts[candidate_id] = vote_counts.get(candidate_id, 0) + 1
            total_votes += 1
    
    # Get candidate names for better display
    candidate_names = {
        'candidate-1': 'Rahul Gandhi (Indian National Congress)',
        'candidate-2': 'Narendra Modi (Bharatiya Janata Party)',
        'candidate-3': 'Arvind Kejriwal (Aam Aadmi Party)',
        'candidate-4': 'Asaduddin Owaisi (AIMIM)'
    }
    
    # Format vote results
    formatted_results = []
    for candidate_id, count in vote_counts.items():
        formatted_results.append({
            'candidate_id': candidate_id,
            'name': candidate_names.get(candidate_id, candidate_id),
            'votes': count,
            'percentage': round((count / total_votes * 100), 2) if total_votes > 0 else 0
        })
    
    # Sort by vote count (highest first)
    formatted_results.sort(key=lambda x: x['votes'], reverse=True)
    
    response = {
        'chain': bc.chain,
        'length': len(bc.chain),
        'total_votes': total_votes,
        'vote_results': formatted_results,
        'pending_votes': len(bc.current_votes)
    }
    return jsonify(response), 200

@app.route('/admin/mine', methods=['POST'])
@admin_required
def mine_block():
    """Mine pending votes into a new block"""
    if not bc.current_votes:
        return jsonify({'message': 'No votes to mine'}), 400
    
    # Simple proof of work (in a real system, this would be more complex)
    last_block = bc.last_block
    last_proof = last_block['proof']
    proof = last_proof + 1
    
    # Create new block with pending votes
    block = bc.new_block(proof)
    
    return jsonify({
        'message': 'New block mined!',
        'index': block['index'],
        'votes': block['votes'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }), 200

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Create tables from models
    app.run(debug=True, port=5001)
