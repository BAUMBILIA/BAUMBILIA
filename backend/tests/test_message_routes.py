import pytest
import datetime
from backend.app import create_app, mongo
from bson import ObjectId
import mongomock
from unittest.mock import patch

@pytest.fixture
def app():
    class TestConfig:
        TESTING = True
        SECRET_KEY = 'test_secret'
        MONGO_URI = 'mongodb://localhost:27017/test_db'
        JWT_SECRET_KEY = 'test_jwt_secret'

    # Patch PyMongo.init_app to avoid real connection attempt
    with patch('flask_pymongo.PyMongo.init_app') as mock_init:
        app = create_app(TestConfig)

        # Manually set up mongomock
        mongo.cx = mongomock.MongoClient()
        mongo.db = mongo.cx.get_database('test_db')

        with app.app_context():
            # Clean up
            mongo.db.messages.delete_many({})
            mongo.db.users.delete_many({})

            yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_header(app):
    user_id = ObjectId()
    # We provide a dummy one to satisfy headers existence if checked
    return {
        'Authorization': f'Bearer dummy_token',
        'user_id': user_id
    }

def test_get_conversation_messages(client, auth_header, app):
    user_id = auth_header['user_id']
    other_user_id = ObjectId()
    conversation_id = ObjectId()

    with app.app_context():
        # Insert users
        mongo.db.users.insert_one({"_id": user_id, "nom": "Me", "prenom": "Myself", "email": "me@myself.com"})
        mongo.db.users.insert_one({"_id": other_user_id, "nom": "Doe", "prenom": "John", "email": "john@doe.com"})

        # Insert sample messages
        messages = [
            {
                "expediteur_id": user_id,
                "destinataire_ids": [other_user_id],
                "conversation_id": conversation_id,
                "corps_message": "Hello",
                "date_envoi": datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
                "statut_lecture": []
            },
            {
                "expediteur_id": other_user_id,
                "destinataire_ids": [user_id],
                "conversation_id": conversation_id,
                "corps_message": "Hi there",
                "date_envoi": datetime.datetime.utcnow(),
                "statut_lecture": []
            },
            # Message from another conversation
            {
                "expediteur_id": user_id,
                "destinataire_ids": [other_user_id],
                "conversation_id": ObjectId(),
                "corps_message": "Other conv",
                "date_envoi": datetime.datetime.utcnow(),
                "statut_lecture": []
            }
        ]
        mongo.db.messages.insert_many(messages)

    # Mock JWT verification and identity retrieval
    with patch('flask_jwt_extended.view_decorators.verify_jwt_in_request'):
        with patch('backend.app.routes.message_routes.get_jwt_identity', return_value={"user_id": str(user_id)}):
            response = client.get(f'/api/messages/conversation/{str(conversation_id)}', headers={'Authorization': auth_header['Authorization']})

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['messages']) == 2
            assert data['messages'][0]['corps_message'] == "Hello"
            assert data['messages'][1]['corps_message'] == "Hi there"
            assert data['total_messages'] == 2

def test_get_conversation_messages_empty(client, auth_header, app):
    conversation_id = ObjectId()
    user_id = auth_header['user_id']

    with patch('flask_jwt_extended.view_decorators.verify_jwt_in_request'):
        with patch('backend.app.routes.message_routes.get_jwt_identity', return_value={"user_id": str(user_id)}):
            response = client.get(f'/api/messages/conversation/{str(conversation_id)}', headers={'Authorization': auth_header['Authorization']})

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['messages']) == 0

def test_get_conversation_messages_unauthorized_participant(client, auth_header, app):
    """Ensure user only sees messages they are part of."""
    user_id = auth_header['user_id']
    other_user_id = ObjectId()
    conversation_id = ObjectId()

    with app.app_context():
        # Message where user is NOT a participant
        mongo.db.messages.insert_one({
            "expediteur_id": other_user_id,
            "destinataire_ids": [ObjectId()], # Some third user
            "conversation_id": conversation_id,
            "corps_message": "Secret",
            "date_envoi": datetime.datetime.utcnow()
        })

    with patch('flask_jwt_extended.view_decorators.verify_jwt_in_request'):
        with patch('backend.app.routes.message_routes.get_jwt_identity', return_value={"user_id": str(user_id)}):
            response = client.get(f'/api/messages/conversation/{str(conversation_id)}', headers={'Authorization': auth_header['Authorization']})

            assert response.status_code == 200
            data = response.get_json()
            assert len(data['messages']) == 0
