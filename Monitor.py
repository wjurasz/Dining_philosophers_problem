import threading
import time
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

N = 5
THINKING = 2
HUNGRY = 1
EATING = 0

states = ['JE', 'CZEKA', 'MYŚLI']
colors = ['green', 'red', 'blue']


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
                self.state[phnum] == HUNGRY):
            self.state[phnum] = EATING
            self.update_callback(phnum, EATING)
            self.log_callback(f"Filozof {phnum} zaczął jeść.")
            self.phcond[phnum].notify()

    def take_fork(self, phnum):
        with self.lock:
            self.state[phnum] = HUNGRY
            self.update_callback(phnum, HUNGRY)
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


class PhilosopherThread(threading.Thread):
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


class PhilosopherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Problem Pięciu Filozofów")
        self.root.configure(bg='black')

        self.labels = []
        self.threads = []
        self.stop_event = threading.Event()

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

        self.start_btn = tk.Button(root, text="Start", command=self.start_threads,
                                   bg='green', fg='white', font=('Helvetica', 14, 'bold'), width=10)
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_threads,
                                  bg='red', fg='white', font=('Helvetica', 14, 'bold'), width=10, state=tk.DISABLED)
        self.stop_btn.pack(pady=5)

        self.log_box = ScrolledText(root, width=80, height=10, bg='black', fg='white', font=('Courier', 10))
        self.log_box.pack(pady=10)
        self.log("=== Logi uruchomienia ===")

        self.monitor = Monitor(self.update_label, self.log)

    def update_label(self, phnum, state):
        def task():
            self.labels[phnum]['text'] = f"Filozof {phnum}\n{states[state]}"
            self.labels[phnum]['bg'] = colors[state]
        self.root.after(0, task)

    def log(self, msg):
        def task():
            self.log_box.insert(tk.END, msg + '\n')
            self.log_box.see(tk.END)
        self.root.after(0, task)

    def start_threads(self):
        self.stop_event.clear()
        self.threads = [PhilosopherThread(i, self.monitor, self.stop_event) for i in range(N)]
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


def main():
    root = tk.Tk()
    app = PhilosopherGUI(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.stop_threads(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
