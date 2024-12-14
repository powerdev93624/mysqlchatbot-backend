from flask import request, Response, Blueprint, stream_with_context, json
from src.middlewares import authentication_required
from src.services.chatgpt_service import get_answer_from_chatgpt
from src.models.user_model import ChatHistory
from src import db
import uuid
from datetime import datetime, timezone

chat = Blueprint("chat", __name__)
@chat.route("/get_response", methods = ["POST"])
@authentication_required
def get_response(auth_data):
    data = request.json
    message = data["message"]
    client_id = auth_data["user_id"]
    user_msg_obj = ChatHistory(
        id=uuid.uuid4(),
        user_id = client_id,
        role = 'user',
        content = message,
        timestamp = datetime.now(timezone.utc)
    )
    db.session.add(user_msg_obj)
    db.session.commit()
    try:
        response = Response(
            stream_with_context(
                get_answer_from_chatgpt(client_id, data["message"])
            )
        )
        response.headers['Content-Type'] = 'application/json'
        response.headers['Transfer-Encoding'] = 'chunked'
        return response
    except Exception as e:
        print(e)
        
@chat.route("/history", methods = ["GET"])
@authentication_required
def get_history(auth_data):
    try:
        client_id = auth_data["user_id"]
        chat_history = ChatHistory.query.filter_by(user_id=client_id).order_by(ChatHistory.timestamp).all()
        payload = [
            {
                "key": chat.id,
                "role": chat.role,
                "content": chat.content,
                "timestamp": chat.timestamp
            }
            for chat in chat_history
        ]
        return Response(
            response=json.dumps({
                    'status': True,
                    "message": "Get history successfully",
                    "payload": payload
                }),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:
        return Response(
            response=json.dumps({
                'status': False,
                "mesage": "Server Error Occured",
                "error": str(e)
            }),
            status=500,
            mimetype='application/json'
        )