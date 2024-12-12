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
        # first validate required use parameters
        
        data = request.json
        print(data)
        if "email" in data and "password" in data:
            # validate if the user exist 
            user = User.query.filter_by(email = data["email"]).first()
            # usecase if the user doesn't exists
            if not user:
                # creating the user instance of User Model to be stored in DB
                user_obj = User(
                    id = uuid.uuid4(),
                    email = data["email"],
                    # hashing the password
                    password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
                )
                db.session.add(user_obj)
                db.session.commit()

                # lets generate jwt token
                payload = {
                    'iat': datetime.now(timezone.utc),
                    'exp': datetime.now(timezone.utc) + timedelta(days=7),
                    'user_id': user_obj.id,
                    'email': user_obj.email,
                }
                token = jwt.encode(payload,os.getenv('SECRET_KEY'), algorithm='HS256')
                return Response(
                    response=json.dumps({
                        'status': True,
                        "message": "User Sign up Successful",
                        "payload": {
                            "token": token
                        }}),
                    status=201,
                    mimetype='application/json'
                )
            else:
                # if user already exists
                return Response(
                response=json.dumps({'status': False, "message": "User already exists kindly use sign in"}),
                status=409,
                mimetype='application/json'
            )
        else:
            # if request parameters are not correct 
            return Response(
                response=json.dumps({'status': False, "message": "User Parameters Firstname, Lastname, Email and Password are required"}),
                status=400,
                mimetype='application/json'
            )
        
    except Exception as e:
        return Response(
            response=json.dumps({'status': False, 
                                    "message": "Error Occured",
                                    "error": str(e)}),
            status=500,
            mimetype='application/json'
        )
    
        

        
