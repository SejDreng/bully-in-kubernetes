import asyncio
from aiohttp import web
import os
import socket
import random
import aiohttp

WEB_PORT = 8080
POD_IP = os.environ.get('POD_IP', socket.gethostbyname(socket.gethostname()))
POD_ID = random.randint(1, 100)
LEADER_ID = None
LEADER_IP = None
POD_HOSTNAME = socket.gethostname()
FIRST_ELECTION = True

class Node():
    def __init__(self, id, leader, leader_ip, hostname):
        self.id = id
        self.hostname = hostname
        self.leader = leader
        self.leader_ip = leader_ip
        self.network = {}  # Dictionary of pod_ip: pod_id
        self.available = True

    async def isalive(self, pod_ip):
        """ Check if a pod is alive by sending a ping request """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'http://{pod_ip}:{WEB_PORT}/ping') as resp:
                    if resp.status == 200:
                        return True
            except Exception as e:
                print(f"Error pinging pod {pod_ip}: {e}")
                return False
        return False

    async def startElection(self):
        """ Start election if no higher-priority nodes are alive """
        # Check if any higher-priority nodes are alive
        higher_nodes =  []
        for pod_ip, pod_id in self.network.items():
            if pod_id > self.id:
                    higher_nodes.append[pod_ip]


        print(f"No higher-priority nodes alive. Starting election.")
        res = []
        for pod_ip, pod_id in higher_nodes:
            result = await self.send_election_request(pod_ip)
            if result:
                res.append(result)
        if res:
            return True
        self.leader = self.id
        await self.setNewLeader()
        return True

    async def send_election_request(self, pod_ip):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'http://{pod_ip}:{WEB_PORT}/receive_election', json={'pod_id': self.id}) as resp:
                    return await resp.json()
            except Exception as e:
                print(f"Error sending election request to {pod_ip}: {e}")
                return False

    async def setNewLeader(self):
        global LEADER_ID
        global LEADER_IP
        LEADER_ID = self.id
        LEADER_IP = POD_IP
        print(f"I am the new leader: {LEADER_ID}, POD hostname is {self.hostname}")
        print("hmmm")
        for pod_ip in self.network.keys():
            print("succes")
            await self.notify_new_leader(pod_ip, self.id, POD_IP ,self.hostname)

    async def notify_new_leader(self, pod_ip, new_leader_id, new_leader_ip, leader_hostname):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f'http://{pod_ip}:{WEB_PORT}/receive_coordinator', json={'leader_id': new_leader_id, 'leader_hostname':leader_hostname, "leader_ip":new_leader_ip}) as resp:
                    return await resp.json()
            except Exception as e:
                print(f"Error notifying new leader to {pod_ip}: {e}")
                return False

async def main_loop(node):
    global LEADER_IP
    global LEADER_ID
    while True:
        print("pik")
        node.leader_ip = LEADER_IP
        node.leader = LEADER_ID
        await asyncio.sleep(2)

        #ping leader
        if node.leader_ip != None:
            leader_liveness = await node.isalive(node.leader_ip)

        #If leader is dead start a new election only once.
        if not leader_liveness and node.leader_ip != None:
            print("Leader is dead. Starting new election.")
            node.leader_ip = None
            await node.startElection()

        #Keep the network updated.
        # Get all pods
        ip_list = []
        try:
            response = socket.getaddrinfo("bully-service", 8080, family=socket.AF_INET)
            for result in response:
                ip = result[-1][0]
                ip_list.append(ip)
            ip_list = list(set(ip_list))
        except Exception as e:
            print(f"Error during DNS lookup: {e}")


        # Remove own POD IP
        if POD_IP in ip_list:
            ip_list.remove(POD_IP)

        # Get IDs of other pods
        await asyncio.sleep(random.randint(1, 5))
        other_pods = dict()
        for pod_ip in ip_list:
            endpoint = '/pod_id'
            url = f'http://{pod_ip}:{WEB_PORT}{endpoint}'
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        json_resp = await resp.json()
                        other_ID = json_resp['pod_id']
                        if other_ID == node.id:
                            node.id = random.randint(1, 100)
                        other_pods[pod_ip] = other_ID
            except Exception as e:
                print(f"Error contacting pod {pod_ip}: {e}")


        # Update node's network
        node.network = other_pods
        print(len(ip_list))
        if(len(ip_list) == 0):
            print("Uwaga the network is empty. Guess I'm the leader now.")
            await node.setNewLeader()

        """
        The below check is necessary when adding multiple new nodes
        to the network at once as sometimes the network is not updated
        quickly enough and a false leader can be set (effectively having
        two leaders.) If a leader node discovers a node with a higher id
        it will start an election.
        """
        for n in node.network:
            if (node.id < n) and LEADER_ID == node.id:
                print("I'm a false leader. Starting election.")
                node.startElection()



async def run_bully():
    global LEADER_ID
    global POD_ID
    global POD_HOSTNAME
    global LEADER_ID
    global LEADER_IP
    node = Node(POD_ID, LEADER_ID, LEADER_IP, POD_HOSTNAME)
    print(f"My ID is: {POD_ID} and my hostname is {POD_HOSTNAME}")
    print("Running bully algorithm")
    await asyncio.sleep(5)  # Wait for everything to be set up

    # Get all pods
    ip_list = []
    print("Making a DNS lookup to service")
    try:
        response = socket.getaddrinfo("bully-service", 8080, family=socket.AF_INET)
        print("Get response from DNS")
        for result in response:
            ip = result[-1][0]
            ip_list.append(ip)
        ip_list = list(set(ip_list))
    except Exception as e:
        print(f"Error during DNS lookup: {e}")


    # Remove own POD IP
    if POD_IP in ip_list:
        ip_list.remove(POD_IP)
    print("Got %d other pod IPs" % len(ip_list))

    # Get IDs of other pods
    await asyncio.sleep(random.randint(1, 5))
    other_pods = dict()
    for pod_ip in ip_list:
        endpoint = '/pod_id'
        url = f'http://{pod_ip}:{WEB_PORT}{endpoint}'
        try:
            async with aiohttp.ClientSession() as session:
                unique = False
                while(not unique):
                    async with session.get(url) as resp:
                        json_resp = await resp.json()
                        other_ID = json_resp['pod_id']
                        if other_ID == node.id:
                            print("I have the same ID as another node. Getting a new one. Current ID: ", other_ID)
                            node.id = random.randint(1, 100)
                            print("Got ID: ", node.id)
                        other_pods[pod_ip] = other_ID
                        unique = True
        except Exception as e:
            print(f"Error contacting pod {pod_ip}: {e}")
            continue


    # Update node's network
    node.network = other_pods

    # Start election
    await node.startElection()

    #Allow the first election to finish so the leader id and ip is set.
    await asyncio.sleep(5)
    await main_loop(node) #It will never exit this loop xd

# HTTP Handlers
async def pod_id(request):
    return web.json_response({'pod_id': POD_ID})

async def receive_election(request):
    global POD_ID, LEADER_ID
    try:
        data = await request.json()
        sender_id = data['pod_id']
        if sender_id < POD_ID:
            print(f"Received election request from pod {sender_id}, responding...")
            return web.json_response(True)
        else:
            print(f"Received election request from pod {sender_id}, not responding.")
            return web.json_response(False)
    except Exception as e:
        print(f"Error in receive_election: {e}")
        return web.json_response(False)

async def receive_coordinator(request):
    global LEADER_ID
    global LEADER_IP
    try:
        data = await request.json()
        LEADER_ID = data['leader_id']
        leader_hostname = data['leader_hostname']
        LEADER_IP = data['leader_ip']
        print(f"New leader elected: {LEADER_ID}. It's hostname is: {leader_hostname}")
        return web.json_response({'status': 'acknowledged'})
    except Exception as e:
        print(f"Error in receive_coordinator: {e}")
        return web.json_response({'status': 'error'})

async def ping(request):
    return web.json_response({'status': 'alive'})

async def background_tasks(app):
    # Ensure web server is running
    await asyncio.sleep(2)
    task1 = asyncio.create_task(run_bully())
    yield
    #task1.cancel()
    await task1
    #task2 =  asyncio.create_task(main_loop())
    #yield
    #await task2

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/pod_id', pod_id)
    app.router.add_post('/receive_election', receive_election)
    app.router.add_post('/receive_coordinator', receive_coordinator)
    app.router.add_get('/ping', ping)  # Add a ping endpoint to check if a node is alive
    app.cleanup_ctx.append(background_tasks)
    web.run_app(app, host='0.0.0.0', port=WEB_PORT)