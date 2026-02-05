import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from bson import ObjectId

# Ensure backend is in path
sys.path.append(os.getcwd())

from flask import Flask

class TestAdminCoursesFilters(unittest.TestCase):

    def setUp(self):
        # Import backend.app to patch its attributes
        # We assume dependencies are installed
        import backend.app

        self.mongo_mock = MagicMock()
        self.bcrypt_mock = MagicMock()

        # Patch mongo and bcrypt in backend.app
        self.mongo_patcher = patch.object(backend.app, 'mongo', self.mongo_mock)
        self.bcrypt_patcher = patch.object(backend.app, 'bcrypt', self.bcrypt_mock)
        self.mongo_patcher.start()
        self.bcrypt_patcher.start()

        # Mock jwt_required and get_jwt_identity from flask_jwt_extended
        self.jwt_patcher = patch('flask_jwt_extended.jwt_required')
        self.jwt_required_mock = self.jwt_patcher.start()

        def mock_jwt_required():
            def decorator(fn):
                def wrapper(*args, **kwargs):
                    return fn(*args, **kwargs)
                return wrapper
            return decorator
        self.jwt_required_mock.side_effect = mock_jwt_required

        self.get_jwt_identity_patcher = patch('flask_jwt_extended.get_jwt_identity')
        self.get_jwt_identity_mock = self.get_jwt_identity_patcher.start()
        self.get_jwt_identity_mock.return_value = {'role': 'admin', 'user_id': 'admin_id'}

        # Now import the module under test
        # We need to reload it if it was already imported to ensure it picks up the patched mongo
        if 'backend.app.routes.admin_routes' in sys.modules:
            import importlib
            import backend.app.routes.admin_routes
            importlib.reload(backend.app.routes.admin_routes)

        from backend.app.routes import admin_routes
        self.admin_routes = admin_routes

        # Create a Flask app context
        self.app = Flask(__name__)
        self.app.register_blueprint(self.admin_routes.admin_bp)
        self.client = self.app.test_client()

    def tearDown(self):
        self.mongo_patcher.stop()
        self.bcrypt_patcher.stop()
        self.get_jwt_identity_patcher.stop()
        self.jwt_patcher.stop()

    def test_get_all_courses_no_filters(self):
        # Setup mock return
        mock_cursor = [
            {
                '_id': ObjectId('507f1f77bcf86cd799439011'),
                'titre': 'Math',
                'filiere_ids': [ObjectId('507f1f77bcf86cd799439012')],
                'professeur_id': ObjectId('507f1f77bcf86cd799439013')
            }
        ]
        self.mongo_mock.db.courses.find.return_value = mock_cursor

        response = self.client.get('/courses')

        self.assertEqual(response.status_code, 200)
        self.mongo_mock.db.courses.find.assert_called_with({})
        self.assertEqual(len(response.json), 1)

    def test_get_all_courses_with_filiere_filter(self):
        fid = '507f1f77bcf86cd799439012'
        self.mongo_mock.db.courses.find.return_value = []

        response = self.client.get(f'/courses?filiere_id={fid}')

        self.assertEqual(response.status_code, 200)
        self.mongo_mock.db.courses.find.assert_called_with({'filiere_ids': ObjectId(fid)})

    def test_get_all_courses_with_professeur_filter(self):
        pid = '507f1f77bcf86cd799439013'
        self.mongo_mock.db.courses.find.return_value = []

        response = self.client.get(f'/courses?professeur_id={pid}')

        self.assertEqual(response.status_code, 200)
        self.mongo_mock.db.courses.find.assert_called_with({'professeur_id': ObjectId(pid)})

    def test_get_all_courses_with_text_filters(self):
        self.mongo_mock.db.courses.find.return_value = []

        response = self.client.get('/courses?niveau=L1&semestre=S1')

        self.assertEqual(response.status_code, 200)
        self.mongo_mock.db.courses.find.assert_called_with({'niveau': 'L1', 'semestre': 'S1'})

    def test_get_all_courses_invalid_id(self):
        response = self.client.get('/courses?filiere_id=invalid')

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalide", response.json['message'])

if __name__ == '__main__':
    unittest.main()
