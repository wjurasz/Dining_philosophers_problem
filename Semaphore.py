import threading
import time
import random
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

philosophers = 5
forks = [threading.Semaphore(1) for _ in range(philosophers)]

states = ['MYŚLI', 'CZEKA', 'JE']
colors = ['blue', 'red', 'green']

class PhilosopherThread(threading.Thread):
    def __init__(self, pid, update_callback, log_callback, state_list, stop_event):
        super().__init__()
        self.pid = pid
        self.update_callback = update_callback
        self.log_callback = log_callback
        self.state_list = state_list
        self.stop_event = stop_event

    def run(self):
        left = self.pid
        right = (self.pid + 1) % philosophers

        while not self.stop_event.is_set():
            self.state_list[self.pid] = 0
            self.update_callback(self.pid, 0)
            self.log_callback(f"Filozof {self.pid} myśli.")
            time.sleep(random.uniform(1, 3))

            self.state_list[self.pid] = 1
            self.update_callback(self.pid, 1)
            self.log_callback(f"Filozof {self.pid} chce podnieść lewy widelec ({left}).")
            forks[left].acquire()
            self.log_callback(f"Filozof {self.pid} zdobył lewy widelec ({left}).")

            self.log_callback(f"Filozof {self.pid} chce podnieść prawy widelec ({right}).")
            forks[right].acquire()

            # Dopiero teraz ustawiamy stan JE i aktualizujemy GUI
            self.state_list[self.pid] = 2
            self.update_callback(self.pid, 2)
            self.log_callback(f"Filozof {self.pid} zdobył prawy widelec ({right}) i zaczął jeść.")

            time.sleep(random.uniform(1, 2))

            forks[left].release()
            forks[right].release()
            self.log_callback(f"Filozof {self.pid} odłożył widelce ({left}, {right}).")

class PhilosopherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Filozofowie przy stole - deadlock version")
        self.root.configure(bg='black')

        self.labels = []
        self.threads = []
        self.states = [0] * philosophers
        self.stop_event = threading.Event()

        self.frame = tk.Frame(root, bg='black')
        self.frame.pack(pady=40)

        for i in range(philosophers):
            label = tk.Label(self.frame, text=f"Filozof {i}\n{states[0]}",
                             bg=colors[0], fg='white', width=18, height=4,
                             font=('Helvetica', 16, 'bold'), relief=tk.RIDGE, bd=3)
            label.grid(row=0, column=i, padx=20, pady=10)
            self.labels.append(label)

        self.start_btn = tk.Button(root, text="Start", command=self.start_threads,
                                   bg='green', fg='white', font=('Helvetica', 14, 'bold'), width=10)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_threads,
                                  bg='red', fg='white', font=('Helvetica', 14, 'bold'), width=10, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.log_box = ScrolledText(root, width=80, height=10, bg='black', fg='white', font=('Courier', 10))
        self.log_box.pack(pady=10)
        self.log("=== Logi uruchomienia ===")

        self.check_deadlock()
        self.check_overeating()

    def update_label(self, pid, state):
        def task():
            self.labels[pid]['text'] = f"Filozof {pid}\n{states[state]}"
            self.labels[pid]['bg'] = colors[state]
        self.root.after(0, task)

    def log(self, msg):
        def task():
            self.log_box.insert(tk.END, msg + '\n')
            self.log_box.see(tk.END)
        self.root.after(0, task)

    def start_threads(self):
        self.stop_event.clear()
        self.threads = [PhilosopherThread(i, self.update_label, self.log, self.states, self.stop_event) for i in range(philosophers)]
        for t in self.threads:
            t.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("Symulacja rozpoczęta.")

    def stop_threads(self):
        self.stop_event.set()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Symulacja zatrzymana.")

    def check_deadlock(self):
        if all(state == 1 for state in self.states):
            self.log("!!! DEADLOCK WYKRYTY - wszyscy filozofowie czekają !!!")
        self.root.after(1000, self.check_deadlock)

    def check_overeating(self):
        eating = sum(1 for s in self.states if s == 2)
        if eating > 2:
            self.log(f"UWAGA: {eating} filozofów je jednocześnie. To nie powinno się zdarzyć!")
        self.root.after(1000, self.check_overeating)

def main():
    root = tk.Tk()
    app = PhilosopherGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_threads(), root.destroy()))
    root.mainloop()

if __name__ == '__main__':
    main()
