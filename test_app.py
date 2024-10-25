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
