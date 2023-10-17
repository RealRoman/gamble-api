from settings import CURSOR, CONNECTION
from fastapi import WebSocket
from models import UserCrash
import json
import random
import time
import asyncio


class WSManager:
    def __init__(self) -> None:
        self.active_connections = {}
        self.game_active = False
        self.current_number = 0
        asyncio.get_event_loop().create_task(self.start_game())

    async def connect(self, user: UserCrash):
        self.active_connections[user.username] = user
        await self.send_message({'case':'user_list', 'user_list': self.get_users()})

    async def disconnect(self, username: str):
        del self.active_connections[username]

    async def send_message(self, message: dict):
        for username, user_obj in self.active_connections.items():
            await user_obj.ws.send_json(message)

    async def recieve_message(self, message: dict, username: str):
        if message['case'] == 'bet' and not self.game_active  and self.active_connections[username].active:
            self.active_connections[username].balance -= message['bet']
            self.active_connections[username].bet = message['bet']
            await self.send_message({'case':'user_list', 'user_list': self.get_users()})
        elif message['case'] == 'crash_end':
            self.active_connections[username].active = False
            self.active_connections[username].balance += round(self.active_connections[username].bet * self.current_number, 2)
            self.active_connections[username].bet = 0
            await self.set_balance(self.active_connections[username].id_user, self.active_connections[username].balance)
            await self.send_message({'case':'user_list', 'user_list': self.get_users()})
        else:
            pass

    def get_users(self):
        user_list = []
        for key, val in self.active_connections.items():
            user_list.append({'username': val.username, 'balance': val.balance, 'bet': val.bet, 'active': val.active})
        return user_list
    
    async def set_users_active(self):
        for key, val in self.active_connections.items():
            val.active = True

    async def end_game(self):
        for key, val in self.active_connections.items():
            if val.bet > 0:
                val.balance -= val.bet
                await self.set_balance(val.id_user, val.balance)
        await self.send_message({'case':'crash_end'})
        await self.send_message({'case':'user_list', 'user_list': self.get_users()})
        self.game_active = False
        
    
    async def start_game(self):
        await self.set_users_active()
        if self.game_active:
            
            random_number = random.randint(0, 100)
            await self.send_message({'case':'crash_start'})
            await self.crash(random_number)

        await asyncio.sleep(10)
        self.game_active = True
        await self.start_game()

    async def crash(self, number):
        self.current_number = 0
        while True:
            await self.send_message({'case':'crash', 'number': self.current_number})
            if self.current_number >= number:
                await self.end_game()
                break
            
            self.current_number += 1
            await asyncio.sleep(0.2)

    async def set_balance(self, id_user: int, balance: int):
        SQL = """
        UPDATE users set balance = %s WHERE id_user = %s
        """
        CURSOR.execute(SQL, params=[balance, id_user])
        CONNECTION.commit()

ws_manager = WSManager()