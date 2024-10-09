from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()



class Investor(db.Model):
    __tablename__ = 'investor'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String(255), nullable=False)  # Password stored in hashed format
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    investment = db.Column(db.Numeric(10, 2), default=200.00)  # Default investment
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    nomineename = db.Column(db.String(100), nullable=False)
    nominee_phone = db.Column(db.String(20), nullable=False)
    profit = db.Column(db.Numeric(10, 2), default=0.00)
    used_gold = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Relationship to bills
    bills = db.relationship('Bill', backref='investor', lazy=True)

    def __repr__(self):
        return f"<Investor {self.fullname}>"

# Bill model
class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    investor_id = db.Column(db.Integer, db.ForeignKey('investor.id'), nullable=False)
    bill_file = db.Column(db.String(255), nullable=False)  # Path to the bill file (PDF)
    profit_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Bill {self.id} - Investor {self.investor_id}>"