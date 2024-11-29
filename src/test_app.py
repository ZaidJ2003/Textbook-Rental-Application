import unittest
from unittest.mock import patch, MagicMock
from app import app, allowed_file
from uuid import uuid4

#200 - Worked
#302 - Redirected
#404 - Not found
class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.user_id = str(uuid4())
        self.cart_id = str(uuid4())
        
        #session data for ALL tests
        with self.app.session_transaction() as sess:
            sess['user'] = {'user_id': self.user_id}
            sess['cart'] = {'cart_id': self.cart_id, 'quantity': 0}

    def test_allowed_file(self):
        self.assertTrue(allowed_file("image.png"))
        self.assertFalse(allowed_file("image.txt"))

    def test_home(self):
        response = self.app.get('/')
        print(f"test_home status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_deleteAccount(self):
        response = self.app.get('/deleteAccount')
        print(f"test_deleteAccount status code: {response.status_code}")
        self.assertEqual(response.status_code, 302)

    def test_addDeleteTextbook(self):
        pass

    def test_add_textbook(self):
        response = self.app.post('/add_textbook', data=dict(
            title='Test Book',
            author='Test Author',
            isbn='1234567890',
            price='9.99'
        ))
        print(f"test_add_textbook status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    @patch('app.db.session.query')
    def test_profile(self, mock_query):
        mock_user = MagicMock()
        mock_user.user_id = self.user_id
        mock_query.return_value.filter.return_value.first.return_value = mock_user
        mock_query.return_value.filter.return_value.all.return_value = []

        response = self.app.get('/profile')
        print(f"test_profile status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_login(self):
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ))
        print(f"test_login status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_register(self):
        response = self.app.post('/register', data=dict(
            username='newuser',
            email='newuser@uncc.edu',
            password='newpassword',
            confirm_password='newpassword'
        ))
        print(f"test_register status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_search(self):
        response = self.app.get('/search', query_string={'query': 'test'})
        print(f"test_search status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    @patch('app.db.session.query')
    def test_book(self, mock_query):
        mock_textbook = MagicMock()
        mock_textbook.id = 1
        mock_query.return_value.filter.return_value.first.return_value = mock_textbook

        response = self.app.get('/book/1')
        print(f"test_book status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    @patch('app.user_repository_singleton.logout_user')
    def test_logout(self, mock_logout_user):
        with self.app.session_transaction() as sess:
            sess['user'] = {'user_id': self.user_id}

        response = self.app.get('/logout')
        print(f"test_logout status code: {response.status_code}")
        self.assertEqual(response.status_code, 302)
        mock_logout_user.assert_called_once()

    @patch('app.db.session.query')
    def test_view_meetup(self, mock_query):
        mock_meetup = MagicMock()
        mock_meetup.id = 1
        mock_query.return_value.filter.return_value.first.return_value = mock_meetup

        response = self.app.get('/meetup/1')
        print(f"test_view_meetup status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    @patch('app.db.session.query')
    def test_load_dms_messages(self, mock_query):
        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_query.return_value.filter.return_value.first.return_value = mock_conversation

        response = self.app.get('/dms/load/1')
        print(f"test_load_dms_messages status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    def test_get_reset_password_page(self):
        response = self.app.get(f'/reset_password/{str(uuid4())}')
        print(f"test_get_reset_password_page status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    def test_reset_password(self):
        response = self.app.post(f'/reset_password/{str(uuid4())}', data=dict(
            password='newpassword',
            confirm_password='newpassword'
        ))
        print(f"test_reset_password status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_get_orders(self):
        response = self.app.get('/orders')
        print(f"test_get_orders status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 200)

    def test_get_rate_textbook_page(self):
        response = self.app.get('/rate/1')
        print(f"test_get_rate_textbook_page status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    def test_about(self):
        response = self.app.get('/about')
        print(f"test_about status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_login_user(self):
        response = self.app.post('/login', data=dict(
            username='testuser',
            password='testpassword'
        ))
        print(f"test_login_user status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_register_user(self):
        response = self.app.post('/register', data=dict(
            username='newuser',
            email='newuser@example.com',
            password='newpassword',
            confirm_password='newpassword'
        ))
        print(f"test_register_user status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_delete_cart_item(self):
        response = self.app.post(f'/cart/delete/{self.cart_id}', data=dict(
            textbook_id=str(uuid4())
        ))
        print(f"test_delete_cart_item status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_update_item_quantity(self):
        response = self.app.post(f'/cart/update/{self.cart_id}', data=dict(
            textbook_id=str(uuid4()),
            textbook_quantity=2
        ))
        print(f"test_update_item_quantity status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    @patch('app.db.session.query')
    def test_view_meetup(self, mock_query):
        mock_meetup = MagicMock()
        mock_meetup.id = 1
        mock_query.return_value.filter.return_value.first.return_value = mock_meetup

        response = self.app.get(f'/view_meetup/{str(uuid4())}')
        print(f"test_view_meetup status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_get_dms_page(self):
        response = self.app.get('/direct_messaging')
        print(f"test_get_dms_page status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_append_message(self):
        response = self.app.post('/direct_messaging', data=dict(
            text='Test message',
            receiver_id=str(uuid4()),
            textbook_id=str(uuid4())
        ))
        print(f"test_append_message status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_load_messages(self):
        response = self.app.get(f'/load_messages/{self.user_id}/{str(uuid4())}')
        print(f"test_load_messages status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 404])

    def test_delete_conversation(self):
        response = self.app.post(f'/conversation/{str(uuid4())}/delete')
        print(f"test_delete_conversation status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_confirm_order(self):
        response = self.app.post(f'/conversation/{str(uuid4())}/confirm')
        print(f"test_confirm_order status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_get_password_request_page(self):
        response = self.app.get('/request_password_reset')
        print(f"test_get_password_request_page status code: {response.status_code}")
        self.assertEqual(response.status_code, 302)

    def test_send_password_request(self):
        response = self.app.post('/request_password_reset', data=dict(
            email='test@example.com'
        ))
        print(f"test_send_password_request status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_get_reset_password_page(self):
        response = self.app.get(f'/reset_password/{str(uuid4())}')
        print(f"test_get_reset_password_page status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_reset_password(self):
        response = self.app.post(f'/reset_password/{str(uuid4())}', data=dict(
            password='newpassword',
            confirm_password='newpassword'
        ))
        print(f"test_reset_password status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    @patch('app.db.session.query')
    def test_get_orders(self, mock_query):
        mock_order = MagicMock()
        mock_order.id = 1
        mock_query.return_value.filter.return_value.all.return_value = [mock_order]

        response = self.app.get('/orders')
        print(f"test_get_orders status code: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_move_order_to_confirmed(self):
        response = self.app.post(f'/orders/{str(uuid4())}/confirm')
        print(f"test_move_order_to_confirmed status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_get_rate_textbook_page(self):
        response = self.app.get(f'/orders/{str(uuid4())}/rate-textbook')
        print(f"test_get_rate_textbook_page status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_submit_rate_textbook_page(self):
        response = self.app.post(f'/orders/{str(uuid4())}/rate-textbook', data=dict(
            rating=5,
            comment='Great book!'
        ))
        print(f"test_submit_rate_textbook_page status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

    def test_create_meetup(self):
        super().setUp()
        self.client = app.test_client()
    
        response = self.client.post('/create_meetup', data={
            'meeting_description': 'Test meeting',
            'start_time': '2024-11-28T3:00',
            'end_time': '2023-11-28T4:00',
            'user_address': '9201 University City Boulevard Charlotte, NC 28223-0001',
            'textbook_id': '1'
        })
        print(f"test_create_meetup status code: {response.status_code}")
        self.assertIn(response.status_code, [200, 302])

#END
if __name__ == '__main__':
    unittest.main()