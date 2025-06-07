import threading
import time
import random
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

N = 5
THINKING = 2
WAITING = 1
EATING = 0

states = ['JE', 'CZEKA', 'MYŚLI']
colors = ['green', 'red', 'blue']

# =============================== MONITOR  ===============================
class Monitor:
    def __init__(self, update_callback, log_callback):
        self.state = [THINKING] * N
        self.lock = threading.Lock()
        self.phcond = [threading.Condition(self.lock) for _ in range(N)]
        self.update_callback = update_callback
        self.log_callback = log_callback

    def test(self, phnum):
        if (self.state[(phnum + 1) % N] != EATING and
                self.state[(phnum + N - 1) % N] != EATING and
                self.state[phnum] == WAITING):
            self.state[phnum] = EATING
            self.update_callback(phnum, EATING)
            self.log_callback(f"Filozof {phnum} zaczął jeść.")
            self.phcond[phnum].notify()

    def take_fork(self, phnum):
        with self.lock:
            self.state[phnum] = WAITING
            self.update_callback(phnum, WAITING)
            self.log_callback(f"Filozof {phnum} chce jeść.")
            self.test(phnum)
            while self.state[phnum] != EATING:
                self.phcond[phnum].wait()

    def put_fork(self, phnum):
        with self.lock:
            self.state[phnum] = THINKING
            self.update_callback(phnum, THINKING)
            self.log_callback(f"Filozof {phnum} odkłada widelce.")
            self.test((phnum + 1) % N)
            self.test((phnum + N - 1) % N)


class MonitorPhilosopherThread(threading.Thread):
    def __init__(self, phnum, monitor, stop_event):
        super().__init__()
        self.phnum = phnum
        self.monitor = monitor
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            time.sleep(1)
            self.monitor.take_fork(self.phnum)
            time.sleep(0.5)
            self.monitor.put_fork(self.phnum)


# =============================== SEMAPHORE  ===============================
class SemaphorePhilosopherThread(threading.Thread):
    def __init__(self, pid, update_callback, log_callback, state_list, stop_event, forks):
        super().__init__()
        self.pid = pid
        self.update_callback = update_callback
        self.log_callback = log_callback
        self.state_list = state_list
        self.stop_event = stop_event
        self.forks = forks
        self.start_time = None  

    def run(self):
        left = self.pid
        right = (self.pid + 1) % N

        while not self.stop_event.is_set():
            if self.start_time is None:
                self.start_time = time.time()

            self.state_list[self.pid] = THINKING
            self.update_callback(self.pid, THINKING)
            self.log_callback(f"Filozof {self.pid} myśli.")
            time.sleep(random.uniform(1, 2))

            self.state_list[self.pid] = WAITING
            self.update_callback(self.pid, WAITING)
            self.log_callback(f"Filozof {self.pid} chce podnieść lewy widelec ({left}).")
            self.forks[left].acquire()
            self.log_callback(f"Filozof {self.pid} zdobył lewy widelec ({left}).")

            # Deadlock po 5 sekundach — filozof NIE PODNOSI prawego widelca
            if time.time() - self.start_time >= 5:
                self.log_callback(f"Filozof {self.pid} czeka na prawy widelec ({right}) — zakleszczenie.")
                while not self.stop_event.is_set():
                    time.sleep(1)
                return

            self.log_callback(f"Filozof {self.pid} chce podnieść prawy widelec ({right}).")
            self.forks[right].acquire()
            self.log_callback(f"Filozof {self.pid} zdobył prawy widelec ({right}) i zaczął jeść.")

            self.state_list[self.pid] = EATING
            self.update_callback(self.pid, EATING)
            time.sleep(random.uniform(1, 2))

            self.forks[left].release()
            self.forks[right].release()
            self.log_callback(f"Filozof {self.pid} odłożył widelce ({left}, {right}).")




# =============================== ARBITER  ===============================
class ArbiterPhilosopherThread(threading.Thread):
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

            self.gui.update_state(self.phnum, WAITING)
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


# =============================== GUI ===============================
class PhilosopherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Problem Pięciu Filozofów")
        self.root.configure(bg='black')
        self.root.geometry("1400x700")
        self.threads = []

        self.selection_frame = tk.Frame(root, bg='black')
        
        self.selection_frame.grid_columnconfigure(0, weight=1)
        self.selection_frame.grid_columnconfigure(1, weight=1)
        self.selection_frame.grid_columnconfigure(2, weight=1)
        self.selection_frame.pack(pady=20, expand=True)
        self.selection_frame.place(relx=0.5, rely=0.3, anchor='center')

        tk.Label(self.selection_frame, text="Wybierz metodę:", font=('Helvetica', 14), fg='white', bg='black').grid(row=0, column=0, columnspan=3, pady=10)

        tk.Button(self.selection_frame, text="Monitor", command=lambda: self.start_simulation("monitor"), font=('Helvetica', 12)).grid(row=1, column=0, padx=10)
        tk.Button(self.selection_frame, text="Semafor", command=lambda: self.start_simulation("semaphore"), font=('Helvetica', 12)).grid(row=1, column=1, padx=10)
        tk.Button(self.selection_frame, text="Arbiter", command=lambda: self.start_simulation("arbiter"), font=('Helvetica', 12)).grid(row=1, column=2, padx=10)

    def setup_simulation_ui(self):
        for widget in self.selection_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(text="Wybierz akcję:")
        self.selection_frame.pack_forget()
        self.labels = []
        self.stop_event = threading.Event()
        self.state_list = [THINKING] * N

        self.forks = [threading.Lock() for _ in range(N)]
        self.sema_forks = [threading.Semaphore(1) for _ in range(N)]
        self.arbiter = threading.Semaphore(N - 1)

        self.frame = tk.Frame(self.root, bg='black')
        self.frame.pack(pady=40)

        for i in range(N):
            label = tk.Label(self.frame, text=f"Filozof {i}\n{states[THINKING]}",
                             bg=colors[THINKING], fg='white', width=18, height=4,
                             font=('Helvetica', 16, 'bold'), relief=tk.RIDGE, bd=3)
            label.grid(row=0, column=i, padx=20, pady=10)
            self.labels.append(label)

        button_frame = tk.Frame(self.root, bg='black')
        button_frame.pack()

        self.stop_btn = tk.Button(button_frame, text="Stop", command=self.stop_simulation,
                                  bg='red', fg='white', font=('Helvetica', 14, 'bold'), width=10)
        self.stop_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.back_btn = tk.Button(button_frame, text="Powrót", command=self.back_to_menu,
                                  bg='blue', fg='white', font=('Helvetica', 14, 'bold'), width=10)
        self.back_btn.pack(side=tk.LEFT, padx=10, pady=5)

        self.log_box = ScrolledText(self.root, width=120, height=10, bg='black', fg='white', font=('Courier', 10))
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

    def stop_simulation(self):
        self.stop_event.set()
        self.log("Symulacja zatrzymana.")

    def back_to_menu(self):
        self.stop_simulation()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.__init__(self.root)

    def start_simulation(self, method):
        self.setup_simulation_ui()
        if method == "monitor":
            monitor = Monitor(self.update_state, self.log)
            self.threads = [MonitorPhilosopherThread(i, monitor, self.stop_event) for i in range(N)]
            self.log("Symulacja (Monitor) rozpoczęta.")
        elif method == "semaphore":
            self.threads = [SemaphorePhilosopherThread(i, self.update_state, self.log, self.state_list, self.stop_event, self.sema_forks) for i in range(N)]
            self.log("Symulacja (Semafor) rozpoczęta.")
        elif method == "arbiter":
            self.threads = [ArbiterPhilosopherThread(i, self, self.forks, self.arbiter, self.stop_event) for i in range(N)]
            self.log("Symulacja (Arbiter) rozpoczęta.")

        for t in self.threads:
            t.start()


# =============================== MAIN ===============================
def main():
    root = tk.Tk()
    app = PhilosopherGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_simulation(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
