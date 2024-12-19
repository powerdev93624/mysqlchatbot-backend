from flask import request, Response, json, Blueprint
from src.models.user_model import Client, ChatHistory
from src import bcrypt, db
from datetime import datetime, timedelta, timezone
from src.middlewares import authentication_required
import jwt
import os
import uuid

user = Blueprint("user", __name__)

@user.route('/users', methods = ["GET"])
def get_users():
    try: 
        clients = Client.query.all()
        payload = [
            {
                "key": client.id,
               "username": client.username,
               "role": "admin" if client.role else "user" 
            }
            for client in clients
        ]
        return Response(
            response=json.dumps({
                    'status': True,
                    "message": "Get data successfully",
                    "payload": payload
                }),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        return Response(
                response=json.dumps({
                    'status': False, 
                    "message": "Server Error Occured",
                    "error": str(e)}),
                status=500,
                mimetype='application/json'
            )
        
        
@user.route('/delete', methods = ["POST"])
def delete_user():
    try: 
        data = request.json
        client = Client.query.filter_by(id=data["id"]).first()
        chat_history = ChatHistory.query.filter_by(user_id=data["id"]).all()
        for chat in chat_history:
            db.session.delete(chat)
        db.session.delete(client)
        db.session.commit()
        return Response(
            response=json.dumps({
                    'status': True,
                    "message": "User has been successfully deleted",
                }),
            status=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        return Response(
                response=json.dumps({
                    'status': False, 
                    "message": "Server Error Occured",
                    "error": str(e)}),
                status=500,
                mimetype='application/json'
            )


        

    
        

        
