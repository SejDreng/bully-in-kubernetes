import unittest
from aiohttp import web, ClientSession
from aiohttp.test_utils import AioHTTPTestCase
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
        #Check that higher reponse is false when we begin.
        higher_init = await self.client.get('/higher_response')
        assert higher_init.status == 200
        state_data_init = await higher_init.json()
        self.assertFalse(state_data_init["higher_response"], "Expected HIGHER_RESPONSE to be True after /receive_answer call")

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
        #Check that initially there isn't a leader.
        leader = await self.client.get('/leader')
        assert leader.status == 200
        state_data = await leader.json()
        self.assertEqual(state_data["leader_ip"], None, "Expected LEADER_IP to be None")
        self.assertEqual(state_data["leader_id"], None, "Expected LEADER_ID to be None")

        # Define test data for the new leader
        new_leader_data = {'leader_ip': '192.168.1.1', 'leader_id': 4321}

        # Send POST request to /receive_coordinator endpoint
        resp = await self.client.post('/receive_coordinator', json=new_leader_data)

        # Assert that we received a 200 OK status from /receive_coordinator
        assert resp.status == 200
        text = await resp.text()
        self.assertEqual(text, "OK", "Expected 'OK' response from /receive_coordinator")

        #Check that the leader has been set correctly.
        leader = await self.client.get('/leader')
        assert leader.status == 200
        state_data = await leader.json()
        self.assertEqual(state_data["leader_ip"], "192.168.1.1", "Expected LEADER_IP to match new leader IP")
        self.assertEqual(state_data["leader_id"], 4321, "Expected LEADER_ID to match new leader ID")

# Run the tests
if __name__ == '__main__':
    unittest.main()



