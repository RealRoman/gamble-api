from models import User
import random
from settings import CURSOR, CONNECTION

class Pexeso:

    def __init__(self) -> None:
        self.active_connections = {}


    def new_game(self, user: User):
        #zapise uzivatele do objektu a vytvori mu cislo
        # hraci plocha je 5 x 5
        # multi znamena kolik uzivatel odhadl spravnych kostek tudiz se jehio balance nasobi
        self.active_connections[user.username] = {}
        self.active_connections[user.username]['x_pos'] = random.randint(0, 4)
        self.active_connections[user.username]['y_pos'] = random.randint(0, 4)
        self.active_connections[user.username]['bet'] = 0
        self.active_connections[user.username]['multi'] = 1
        print(self.active_connections)

    def guess(self, user: User, x_pos: int, y_pos: int, bet: int):
        print(bet)
        # pristupuje k nasobici, pokud uhodne spatne zavola new_game
        user_dict = self.active_connections[user.username]
        user_dict['bet'] += bet
        if (x_pos is user_dict['x_pos'] and y_pos is user_dict['y_pos']):
            balance = user.balance - user_dict['bet']
            self.set_balance(user, balance=balance)
            self.new_game(user)
            print(self.active_connections)
            return True
        
        else:
            user_dict['multi'] *= 1.2
            print(self.active_connections)
            return False
        
        
    def end_game(self, user: User):
        user_dict = self.active_connections[user.username]
        balance = user.balance + (user_dict['bet'] * user_dict['multi'])
        self.set_balance(user, balance)
        self.new_game(user)

    def disconnect(self, user: User):
        # po odhlaseni uzivatele odstrani uzivatele
        try:
            del self.active_connections[user.username]
        except:
            pass

    def set_balance(self, user: User, balance: int):
        SQL = """
        UPDATE users set balance = %s WHERE id_user = %s
        """
        CURSOR.execute(SQL, params=[balance, user.id_user])
        CONNECTION.commit()


pexeso_manager = Pexeso()