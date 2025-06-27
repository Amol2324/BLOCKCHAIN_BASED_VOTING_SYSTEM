from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Voter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    voter_id = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    has_voted = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Voter {self.voter_id}>'
