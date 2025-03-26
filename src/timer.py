import customtkinter as ctk
import tkinter as tk 
import subprocess
import platform

TIMES = ["00:30", "01:00", "02:00", "03:00"]

class Timer:
    def __init__(self,parent_tk):
        self.timer_window = ctk.CTkToplevel(parent_tk)
        self.timer_window.title("Timer")
        self.timer_window.geometry("300x200")
        self.timer_window.attributes("-topmost", True)

        self.timer_window.remaining_time = tk.StringVar(value=TIMES[0])
        self.timer_window.timer_running = False
        self.timer_window.timer_id = None
        
        self.timer_label = ctk.CTkLabel(self.timer_window, text=self.timer_window.remaining_time.get(), font=ctk.CTkFont(size=32, weight="bold"))
        self.timer_label.pack(pady=(20, 10))

        self.time_selector = ctk.CTkComboBox(self.timer_window, values=TIMES)
        self.time_selector.set(TIMES[0])
        self.time_selector.pack()

        self.start_pause_button = ctk.CTkButton(self.timer_window, text="Start", command=self.toggle_timer)
        self.start_pause_button.pack(pady=10)

        self.reset_button = ctk.CTkButton(self.timer_window, text="Reset", command=self.reset_timer)
        self.reset_button.pack()

    def format_time(self,seconds):
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02}:{secs:02}"

    def parse_time_string(self,time_str):
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds

    def update_timer_display(self):
        self.timer_label.configure(text=self.timer_window.remaining_time.get())

    def countdown(self):
        time_left = self.parse_time_string(self.timer_window.remaining_time.get())
        if time_left > 0:
            time_left -= 1
            self.timer_window.remaining_time.set(self.format_time(time_left))
            self.update_timer_display()
            self.timer_window.timer_id = self.timer_window.after(1000, self.countdown)
        else:
            self.timer_window.timer_running = False
            if platform.system() == "Darwin":
                subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"])

    def toggle_timer(self):
        if self.timer_window.timer_running:
            if self.timer_window.timer_id:
                self.timer_window.after_cancel(self.timer_window.timer_id)
            self.timer_window.timer_running = False
            self.start_pause_button.configure(text="Start")
        else:
            # Add 3-second countdown in red if timer is at starting value
            if self.timer_window.remaining_time.get() == self.time_selector.get():
                self.countdown_start(3)
            else:
                self.timer_window.timer_running = True
                self.start_pause_button.configure(text="Pause")
                self.countdown()

    def countdown_start(self, count):
        if count > 0:
            self.timer_label.configure(text=f"{count}", text_color="red")
            self.timer_window.timer_id = self.timer_window.after(1000, lambda: self.countdown_start(count - 1))
        else:
            self.timer_label.configure(text=self.timer_window.remaining_time.get(), text_color="white")
            self.timer_window.timer_running = True
            self.start_pause_button.configure(text="Pause")
            self.countdown()

    def reset_timer(self):
        if self.timer_window.timer_id:
            self.timer_window.after_cancel(self.timer_window.timer_id)
        self.timer_window.timer_running = False
        self.timer_window.remaining_time.set(self.time_selector.get())
        self.update_timer_display()
        self.start_pause_button.configure(text="Start")