import asyncio
from aiohttp import web
import os
import socket
import random
import aiohttp
import requests

POD_IP = str(os.environ['POD_IP'])
#POD_IP = socket.gethostbyname(socket.gethostname())
WEB_PORT = int(os.environ['WEB_PORT'])
#WEB_PORT = 8080
POD_ID = random.randint(0, 100)
LEADER = False
HIGHER_REPONSE = False
MAX_TIMEOUT = 5
other_pods = dict()

async def setup_k8s():
    # If you need to do setup of Kubernetes, i.e. if using Kubernetes Python client
	print("K8S setup completed")
 
async def run_bully():
    global other_pods
    leader_alive = False
    while True:
        print("Running bully")
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        ip_list = []
        print("Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        print("Get response from DNS")
        for result in response:
            ip_list.append(result[-1][0])
        ip_list = list(set(ip_list))
        
        # Remove own POD ip from the list of pods
        ip_list.remove(POD_IP)
        print("Got %d other pod ip's" % (len(ip_list)))
        
        # Get ID's of other pods by sending a GET request to them
        await asyncio.sleep(random.randint(1, 5))
        for pod_ip in ip_list:
                endpoint = '/pod_id'
                url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
                response = requests.get(url)
                print("Got response: ", response)
                other_pods[str(pod_ip)] = response.json()
            
        # Other pods in network
        print("Other pods:")
        print(other_pods)
           
        if not leader_alive:
            HIGHER_REPONSE = False
            # Start election
            #await start_election()
            await start_election()
            await asyncio.sleep(MAX_TIMEOUT)
            if not HIGHER_REPONSE:
                #I'm the leader.
                pass


        # Sleep cock repeat
        #"Min morgen rutine:
        #Vågn op
        #Lav en lort
        #spis
        #stå ud af sengen
        #lav morgenmad"
        # - valder hvid
        # Ja videnskab kælling!
        await asyncio.sleep(2)
    


async def start_election():
    global other_pods
    print("Starting election")
    print("I got the other pods\n", other_pods)
    for pod_ip, pod_id in other_pods.items():
        print("checking pod: ", pod_ip)
        #pod_id = other_pods[str(pod_ip)]
        if pod_id > POD_ID:
            print("contacting pod: ", pod_ip)
            endpoint = '/receive_election'
            url = 'http://' + str(pod_ip) + ':' + str(WEB_PORT) + endpoint
            await asyncio.sleep(random.randint(0, 100)*0.01)
            requests.post(url, json={'pod_ip' : POD_IP})
            await asyncio.sleep(1)
            print("I've sent an election message.")


#GET /pod_id
async def pod_id(request):
    return web.json_response(POD_ID)
    
#POST /receive_answer
async def receive_answer(request):
    return web.json_response(text="OK")
    global LEADER
    global HIGHER_REPONSE
    print("Sut den Simon")
    data = await request.json()
    other_id = data['pod_id']
    print("Got a \"OK\" reponse from ", other_id)
    print("I'm not the leader")
    LEADER = False
    HIGHER_REPONSE = True
    
#POST /receive_election
async def receive_election(request):
    return web.json_response(text="OK")
    #request = callee pod
    print("Got reponse ", request)
    data = await request.json()
    print(data)
    resp_ip = data["pod_ip"]
    endpoint = "/receive_answer"
    url = 'http://' + str(resp_ip) + ':' + str(WEB_PORT) + endpoint
    requests.post(url, json={"pod_id" : POD_ID})
    #start_election()
    return web.HTTPOk
    
    
#POST /receive_coordinator
async def receive_coordinator(request):
    pass

async def background_tasks(app):
    print("pik1")
    task = asyncio.create_task(run_bully())

    try:
        # Keep the background task running
        yield
    finally:
        # This block is executed during shutdown
        print("Cancelling background task")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Background task cancelled")
    """
    print("pik2")
    yield
    print("penis")
    #task.cancel()
    print("pik3")
    await task
    print("pik4")
    """

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/pod_id', pod_id)
    app.router.add_post('/receive_answer', receive_answer)
    app.router.add_post('/receive_election', receive_election)
    app.router.add_post('/receive_coordinator', receive_coordinator)
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=WEB_PORT)
    
    
