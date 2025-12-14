from threading import Thread, current_thread, Lock
import random as r
import time

class Account:
    def __init__(self, balance=0):
        self.balance = balance
        self.account_lock = Lock()

    def deposit(self, amount):
        with self.account_lock:
            if amount < 0:
                if self.balance >= -amount:
                    new_balance = self.balance + amount
                    print(f"Withdrawing {-amount}...")
                else:
                    new_balance = self.balance
                    print("Insufficient balance, can't withdraw", -amount)

            else :
                new_balance = self.balance + amount
                print(f"Depositing {amount}...")

            self.balance = new_balance

            time.sleep(r.random())  # Simulate a delay

if __name__ == "__main__":

    account = Account(1000)

    threads = []
    actions = [200,-2000,-500,600]
    
    for a in actions:
        thread = Thread(target = account.deposit, args=[a])
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print(f"Account balance is", account.balance)