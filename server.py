import os
import random
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
from typing import List

app = FastAPI()

# ----------------------------
# Observer Pattern
# ----------------------------

class Observer:
    def __init__(self, name: str):
        self.name = name

    async def update(self, state: str, from_machine: str):
        pass


class Subject:
    def __init__(self):
        self._observers: List[Observer] = []
        self.state = "IDLE"

    def attach(self, observer: Observer):
        self._observers.append(observer)

    async def notify_all_observers(self):
        for observer in self._observers:
            await observer.update(self.state, self.name)

    async def setState(self, state: str):
        self.state = state
        await self.notify_all_observers()


class Machine(Subject):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class Dashboard(Observer):
    def __init__(self):
        super().__init__("Dashboard")
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def update(self, state: str, from_machine: str):
        message = {
            "machine": from_machine,
            "state": state
        }
        for connection in self.active_connections:
            await connection.send_json(message)


# ----------------------------
# Machine Setup
# ----------------------------

dashboard = Dashboard()

machineA = Machine("Machine A")
machineB = Machine("Machine B")
machineC = Machine("Machine C")

machines = [machineA, machineB, machineC]

for m in machines:
    m.attach(dashboard)

STATES = ["PRODUCING", "IDLE", "STARVED"]


async def machine_state_loop():
    while True:
        await asyncio.sleep(3)
        machine = random.choice(machines)
        new_state = random.choice(STATES)
        await machine.setState(new_state)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(machine_state_loop())


# ----------------------------
# Routes
# ----------------------------

@app.get("/")
async def root():
    return FileResponse("index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await dashboard.connect(websocket)
    while True:
        await asyncio.sleep(100)


# ----------------------------
# Run Server
# ----------------------------

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port)
