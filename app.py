import asyncio
from aiohttp import web
import os
import socket
import random
import aiohttp
import time
import requests

POD_IP = str(os.environ['POD_IP'])
#POD_IP = socket.gethostbyname(socket.gethostname())
WEB_PORT = int(os.environ['WEB_PORT'])
#WEB_PORT = 8080
POD_ID = random.randint(0, 10000)
HIGHER_RESPONSE = False
MAX_TIMEOUT = 5
other_pods = dict()
LEADER_IP = None
LEADER_ID = None
LEADER_ALIVE = False

 
async def run_bully():
    global other_pods
    global LEADER_IP
    global LEADER_ID
    global POD_ID
    global POD_IP
    global LEADER_ALIVE
    global HIGHER_RESPONSE
    time_last_election = time.time() - 30
    while True:
        #Useful debugging information
        print("Running bully")
        print("My id is:", POD_ID)
        print("My ip is:", POD_IP)
        if LEADER_IP != None: print("My leader is ", LEADER_ID)
        await asyncio.sleep(5) # wait for everything to be up
        
        # Get all pods doing bully
        ip_list = []
        print("Making a DNS lookup to service")
        response = socket.getaddrinfo("bully-service",0,0,0,0)
        print("Get response from DNS")
        print(response)
        for result in response:
            ip_list.append(result[-1][0])
        ip_list = list(set(ip_list))

        
        # Remove own POD ip from the list of pods 
        # (If it exists. When scaling it takes a short while for the IP to be added.)
        if POD_IP in ip_list: ip_list.remove(POD_IP)
        print("Got %d other pod ip's" % (len(ip_list)))

        
        # Get ID's of other pods by sending a GET request to them
        other_pods.clear()
        async with aiohttp.ClientSession() as session:
            for pod_ip in ip_list:
                endpoint = '/pod_id'
                url = f'http://{pod_ip}:{WEB_PORT}{endpoint}'
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            pod_data = await response.json()
                            print("Got response: ", pod_data)
                            if pod_data == POD_ID:
                                print("Got an ID collision. Giving myself a new ID")
                                POD_ID = random.randint(0,10000)
                            other_pods[str(pod_ip)] = pod_data
                except Exception as e:
                    print(f"Failed to get pod_id from {pod_ip}: {e}")
            
        # Other pods in network
        print("Other pods:")
        print(other_pods)

        #If the pods is not the leader it should check if the leader is still alive.
        if LEADER_IP != None and LEADER_IP != POD_IP:
            async with aiohttp.ClientSession() as session:
                endpoint = '/pod_id'
                url = f'http://{LEADER_IP}:{WEB_PORT}{endpoint}'
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            print("Leader is still alive")
                            LEADER_ALIVE = True
                except Exception as e:
                    print("Leader is not alive")
                    LEADER_ALIVE = False

        #If the leader is not alive a new election should be started.
        time_diff = time.time() - time_last_election
        if not LEADER_ALIVE and time_diff > 30:
            HIGHER_RESPONSE = False
            # Start election
            time_last_election = time.time()
            print("Time is ", time_last_election)
            await start_election()
            await asyncio.sleep(MAX_TIMEOUT)
            
            #If we to this point and HIGHER_RESPONSE is False it means we didn't get
            #any acknowlegdements (OKs) back and therefore we are the leader.
            if not HIGHER_RESPONSE:
                #I'm the leader.
                LEADER_ID = POD_ID
                LEADER_IP = POD_IP
                #Contact all the other pods and let them know we are the new leader.
                async with aiohttp.ClientSession() as session:
                    print(f"I'm to become the leader.")
                    for pod_ip, _ in other_pods.items():
                        endpoint = '/receive_coordinator'
                        url = f'http://{pod_ip}:{WEB_PORT}{endpoint}'
                        try:
                            await asyncio.sleep(random.uniform(0, 1))  # Simulating random delay
                            async with session.post(url, json={'leader_ip': POD_IP, 'leader_id': POD_ID}) as response:
                                if response.status == 200:
                                    print("Sent leader coordinator message.")
                        except Exception as e:
                            print(f"Failed to contact {pod_ip}: {e}")
                    
                
                

        await asyncio.sleep(2)
    

#Function to start an alection- Sends a post with receive election to all pods in the
#network with a higher ID than the current pod.
async def start_election():
    global other_pods
    other_pods = {k: v for k, v in sorted(other_pods.items(), key=lambda item: item[1], reverse=True)}
    print("Sorted:\n",other_pods)
    print("Starting election")
    async with aiohttp.ClientSession() as session:
        for pod_ip, pod_id in other_pods.items():
            print(f"Checking pod: {pod_ip} with pod_id {pod_id}")
            if pod_id > POD_ID:
                print(f"Contacting pod: {pod_ip}")
                endpoint = '/receive_election'
                url = f'http://{pod_ip}:{WEB_PORT}{endpoint}'
                try:
                    await asyncio.sleep(random.uniform(0, 1))  # Simulating random delay
                    async with session.post(url, json={'pod_ip': POD_IP, 'pod_id': POD_ID}) as response:
                        if response.status == 200:
                            print("I've sent an election message.")
                except Exception as e:
                    print(f"Failed to contact {pod_ip}: {e}")


#GET /pod_id
async def pod_id(request):
    return web.json_response(POD_ID)
    
#POST /receive_answer
#This function lets a pod know that it got it's election message and that it's alive.
async def receive_answer(request):
    global HIGHER_RESPONSE
    data = await request.json()
    other_id = data['pod_id']
    print(f"Got an 'OK' response from {other_id}")
    print("I'm not the leader")
    HIGHER_RESPONSE = True
    return web.json_response(text="OK")
    
#POST /receive_election
#This function lets a pod now an election has been started and they should repond OK
#So the sender know's they're alive and doesn't become the leader.
async def receive_election(request):
    global LEADER_ALIVE
    LEADER_ALIVE = False
    print("Received election message")
    data = await request.json()
    resp_ip = data["pod_ip"]
    resp_id = data['pod_id']
    print(f"Election started by {resp_id}")
    # Respond with an OK message
    endpoint = "/receive_answer"
    url = f'http://{resp_ip}:{WEB_PORT}{endpoint}'
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={"pod_id": POD_ID})
    return web.json_response(text="OK")
    
    
#POST /receive_coordinator
#This function lets a pod know who the new leader is.
async def receive_coordinator(request):
    global LEADER_IP
    global LEADER_ID
    data = await request.json()
    LEADER_ID = data['leader_id']
    LEADER_IP = data['leader_ip']
    print("Got a new leader: ", LEADER_ID)
    return web.json_response(text="OK")


async def background_tasks(app):
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
    
    
