# import pytest
# from aiohttp import web
# from unittest.mock import patch
# from app import receive_election, receive_answer, receive_coordinator, pod_id

# @pytest.fixture
# def test_app():
#     app = web.Application()
#     app.router.add_get('/pod_id', pod_id)
#     app.router.add_post('/receive_answer', receive_answer)
#     app.router.add_post('/receive_election', receive_election)
#     app.router.add_post('/receive_coordinator', receive_coordinator)
#     return app

# @pytest.mark.asyncio
# async def test_receive_election(test_app, aiohttp_client):
#     client = await aiohttp_client(test_app)
#     # Patch LEADER_ALIVE to simulate election behavior
#     with patch('app.LEADER_ALIVE', False):
#         response = await client.post('/receive_election', json={'pod_ip': '127.0.0.1', 'pod_id': 200})
#         assert response.status == 200
#         response_text = await response.text()
#         assert response_text == "OK"
#         test_app['LEADER_ALIVE']
#         # After receiving an election message, LEADER_ALIVE should be False
#         assert test_app['LEADER_ALIVE'] == False

# @pytest.mark.asyncio
# async def test_receive_answer(test_app, aiohttp_client):
#     client = await aiohttp_client(test_app)
#     # Patch HIGHER_RESPONSE to initially be False
#     with patch('app.HIGHER_RESPONSE', False):
#         response = await client.post('/receive_answer', json={'pod_id': 200})
#         assert response.status == 200
#         response_text = await response.text()
#         assert response_text == "OK"
#         # After receiving an answer, HIGHER_RESPONSE should be set to True
#         assert test_app.HIGHER_RESPONSE is True

# @pytest.mark.asyncio
# async def test_receive_coordinator(test_app, aiohttp_client):
#     client = await aiohttp_client(test_app)
#     # Patch LEADER_ID and LEADER_IP for initial setup
#     with patch('app.LEADER_ID', None), patch('app.LEADER_IP', None):
#         response = await client.post('/receive_coordinator', json={'leader_ip': '127.0.0.1', 'leader_id': 300})
#         assert response.status == 200
#         response_text = await response.text()
#         assert response_text == "OK"
#         # Verify that LEADER_ID and LEADER_IP have been updated with the new leader's information
#         assert test_app.LEADER_ID == 300
#         assert test_app.LEADER_IP == '127.0.0.1'

import asyncio
import unittest
from aiohttp import web, ClientSession
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from unittest.mock import patch
import app as appp
import socket

# Assuming the main app module is named 'bully_algorithm'
# from bully_algorithm import app, receive_answer, HIGHER_RESPONSE, POD_ID

# We need to import or define receive_answer and the global variables used here:
# Since HIGHER_RESPONSE is a global, we need to reset it for each test.

# Define test class
class TestReceiveAnswer(AioHTTPTestCase):

    async def get_application(self):
        # Return the application that should be tested
        app = web.Application()
        app.router.add_get('/pod_id', appp.pod_id)
        app.router.add_post('/receive_answer', appp.receive_answer)
        app.router.add_post('/receive_election', appp.receive_election)
        app.router.add_post('/receive_coordinator', appp.receive_coordinator)
        app.router.add_get('/higher_response', appp.get_higher_response)
        app.router.add_get('/leader_alive', appp.get_leader_alive) 
        app.router.add_get('/leader', appp.get_leader) 
        return app

    
    #@unittest_run_loop
    async def test_receive_answer_sets_higher_response(self):
        # Initial state should be False

        # Define test data
        test_data = {'pod_id': 1234}
        
        # Send POST request to /receive_answer endpoint
        resp = await self.client.post('/receive_answer', json=test_data)
        
        # Assert response is OK and content is as expected
        assert resp.status == 200
        text = await resp.text()
        self.assertEqual(text, "OK", "Expected 'OK' response from /receive_answer")

        # Check the state of HIGHER_RESPONSE on the pod


        higher = await self.client.get('/higher_response')
        assert higher.status == 200
        state_data = await higher.json()
        self.assertTrue(state_data["higher_response"], "Expected HIGHER_RESPONSE to be True after /receive_answer call")

          
    #@unittest_run_loop
    async def test_receive_election(self):
        # Define test data for election
        ip = socket.gethostbyname(socket.gethostname())
        election_data = {'pod_ip': str(ip), 'pod_id': 1234}
        

        #async with ClientSession() as session:
        #    async with session.post('/receive_election', json=election_data) as response_state:
        #        assert response_state.status == 200
        #        text = await response_state.text()
        #        self.assertEqual(text, "OK", "Expected 'OK' response from /receive_election")


        # Send POST request to /receive_election endpoint
        resp = await self.client.post('/receive_election', json=election_data)
        
        # Assert that we received a 200 OK status from the /receive_election endpoint
        assert resp.status == 200
        text = await resp.text()
        self.assertEqual(text, "OK", "Expected 'OK' response from /receive_election")


        # Now check the state of LEADER_ALIVE to ensure it's set to False
        alive = await self.client.get('/leader_alive')
        assert alive.status == 200
        state_data = await alive.json()
        self.assertFalse(state_data["leader_alive"], "Expected LEADER_ALIVE to be False after /receive_election call")


    async def test_receive_coordinator_updates_leader(self):
        # Define test data for the new leader
        new_leader_data = {'leader_ip': '192.168.1.1', 'leader_id': 4321}

        # Send POST request to /receive_coordinator endpoint
        resp = await self.client.post('/receive_coordinator', json=new_leader_data)

        # Assert that we received a 200 OK status from /receive_coordinator
        assert resp.status == 200
        text = await resp.text()
        self.assertEqual(text, "OK", "Expected 'OK' response from /receive_coordinator")

        leader = await self.client.get('/leader')
        assert leader.status == 200
        state_data = await leader.json()
        self.assertEqual(state_data["leader_ip"], "192.168.1.1", "Expected LEADER_IP to match new leader IP")
        self.assertEqual(state_data["leader_id"], 4321, "Expected LEADER_ID to match new leader ID")

# Run the tests
if __name__ == '__main__':
    unittest.main()



