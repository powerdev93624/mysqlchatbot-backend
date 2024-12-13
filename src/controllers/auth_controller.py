from flask import request, Response, json, Blueprint
from src.models.user_model import Client
from src import bcrypt, db
from datetime import datetime, timedelta, timezone
from src.middlewares import authentication_required
import jwt
import os
import uuid

auth = Blueprint("auth", __name__)

@auth.route('/signin', methods = ["POST"])
def handle_login():
    try: 
        data = request.json
        print(data)
        if "username" and "password" in data:
            client = Client.query.filter_by(username = data["username"]).first()
            if client:
                if bcrypt.check_password_hash(client.password, data["password"]):
                    payload = {
                        'iat': datetime.now(timezone.utc),
                        'exp': datetime.now(timezone.utc) + timedelta(days=7),
                        'user_id': client.id,
                        'username': client.username,
                        'role': client.role
                    }
                    token = jwt.encode(payload,os.getenv('SECRET_KEY'),algorithm='HS256')
                    return Response(
                            response=json.dumps({
                                    'status': True,
                                    "message": "Sign In Successful",
                                    "payload": {
                                        "token": token
                                    }
                                }),
                            status=200,
                            mimetype='application/json'
                        )
                else:
                    return Response(
                        response=json.dumps({'status': False, "message": "Password Mistmatched"}),
                        status=401,
                        mimetype='application/json'
                    ) 
            # if there is no user record
            else:
                return Response(
                    response=json.dumps({'status': False, 
                        "message": "User Record doesn't exist."}),
                    status=404,
                    mimetype='application/json'
                ) 
        else:
            # if request parameters are not correct 
            return Response(
                response=json.dumps({'status': False, "message": "User Parameters Username and Password are required"}),
                status=400,
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

        
@auth.route('/signup', methods = ["POST"])
def handle_signup():
    try: 
        data = request.json
        print(data)
        if "username" in data and "password" in data:
            client = Client.query.filter_by(username = data["username"]).first()
            if not client:
                client_obj = Client(
                    id = uuid.uuid4(),
                    username = data["username"],
                    password = bcrypt.generate_password_hash(data['password']).decode('utf-8'),
                    role = True if data["role"] == "admin" else False
                )
                db.session.add(client_obj)
                db.session.commit()
                payload = {
                    'iat': datetime.now(timezone.utc),
                    'exp': datetime.now(timezone.utc) + timedelta(days=7),
                    'client_id': client_obj.id,
                    'username': client_obj.username,
                    'role': client_obj.role
                }
                token = jwt.encode(payload,os.getenv('SECRET_KEY'), algorithm='HS256')
                return Response(
                    response=json.dumps({
                        'status': True,
                        "message": "Sign up Successful",
                        "payload": {
                            "token": token,
                            "id": client_obj.id
                        }}),
                    status=201,
                    mimetype='application/json'
                )
            else:
                # if user already exists
                return Response(
                response=json.dumps({'status': False, "message": "User already exists."}),
                status=409,
                mimetype='application/json'
            )
        else:
            return Response(
                response=json.dumps({'status': False, "message": "User Parameters Username and Password are required"}),
                status=400,
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
    
        

        
