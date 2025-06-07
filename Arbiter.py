import threading
import time
import random
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

N = 5
THINKING = 2
HUNGRY = 1
EATING = 0

states = ['JE', 'CZEKA', 'MYŚLI']
colors = ['green', 'red', 'blue']

class PhilosopherThread(threading.Thread):
    def __init__(self, phnum, gui, forks, arbiter, stop_event):
        super().__init__()
        self.phnum = phnum
        self.gui = gui
        self.forks = forks
        self.arbiter = arbiter
        self.stop_event = stop_event

    def run(self):
        left = self.phnum
        right = (self.phnum + 1) % N

        while not self.stop_event.is_set():
            self.gui.update_state(self.phnum, THINKING)
            self.gui.log(f"Filozof {self.phnum} myśli.")
            time.sleep(random.uniform(1, 2))

            self.gui.update_state(self.phnum, HUNGRY)
            self.gui.log(f"Filozof {self.phnum} prosi o widelec.")
            self.arbiter.acquire()

            self.forks[left].acquire()
            self.forks[right].acquire()

            self.gui.update_state(self.phnum, EATING)
            self.gui.log(f"Filozof {self.phnum} je.")
            time.sleep(random.uniform(1, 2))

            self.forks[left].release()
            self.forks[right].release()
            self.arbiter.release()

class PhilosopherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Problem Pięciu Filozofów - Semafor")
        self.root.configure(bg='black')

        self.labels = []
        self.threads = []
        self.stop_event = threading.Event()

        self.forks = [threading.Lock() for _ in range(N)]
        self.arbiter = threading.Semaphore(N - 1)

        self.frame = tk.Frame(root, bg='black')
        self.frame.pack(pady=40)

        for i in range(N):
            label = tk.Label(self.frame,
                             text=f"Filozof {i}\n{states[THINKING]}",
                             bg=colors[THINKING],
                             fg='white',
                             width=18,
                             height=4,
                             font=('Helvetica', 16, 'bold'),
                             relief=tk.RIDGE,
                             bd=3)
            label.grid(row=0, column=i, padx=20, pady=10)
            self.labels.append(label)

        self.start_btn = tk.Button(root, text="Start", command=self.start_simulation,
                                   bg='green', fg='white', font=('Helvetica', 14, 'bold'), width=10)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_simulation,
                                  bg='red', fg='white', font=('Helvetica', 14, 'bold'), width=10, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.log_box = ScrolledText(root, width=80, height=10, bg='black', fg='white', font=('Courier', 10))
        self.log_box.pack(pady=10)
        self.log("=== Logi uruchomienia ===")

    def update_state(self, phnum, state):
        def task():
            self.labels[phnum]['text'] = f"Filozof {phnum}\n{states[state]}"
            self.labels[phnum]['bg'] = colors[state]
        self.root.after(0, task)

    def log(self, msg):
        def task():
            self.log_box.insert(tk.END, msg + '\n')
            self.log_box.see(tk.END)
        self.root.after(0, task)

    def start_simulation(self):
        self.stop_event.clear()
        self.threads = [PhilosopherThread(i, self, self.forks, self.arbiter, self.stop_event) for i in range(N)]
        for t in self.threads:
            t.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("Symulacja rozpoczęta.")

    def stop_simulation(self):
        self.stop_event.set()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Symulacja zatrzymana.")

def main():
    root = tk.Tk()
    app = PhilosopherGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_simulation(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()
