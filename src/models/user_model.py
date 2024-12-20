from src import db
from datetime import datetime, timezone

class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.String(50), primary_key = True, unique=True)
    username = db.Column(db.String(70), unique = True)
    password = db.Column(db.String(80))
    role = db.Column(db.Boolean, default=True)
    # email = db.Column(db.String(120), unique=True)
    # chathistory = db.Column(db.Text(4294967295))
    # plaid_access_key = db.Column(db.String(255))
    # plaid_item_id = db.Column(db.String(255))
    # plaid_data = db.Column(db.Text(4294967295))
class ChatHistory(db.Model):
    __tablename__ = "chathistory"
    id = db.Column(db.String(50), primary_key = True, unique=True)
    user_id = db.Column(db.String(50), db.ForeignKey('clients.id'), nullable=False)
    role = db.Column(db.String(50), default=True)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    

# class SecondDBModel(db.Model):
#     __bind_key__ = 'db2'
#     id = db.Column(db.Integer, primary_key=True)
#     data = db.Column(db.String(80))

# # Model using third database
# class ThirdDBModel(db.Model):
#     __bind_key__ = 'db3'
#     id = db.Column(db.Integer, primary_key=True)
#     info = db.Column(db.String(80))