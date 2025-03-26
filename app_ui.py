import customtkinter as ctk
import tkinter as tk  # add this at the top

import ollama
import json
import os
from datetime import datetime
import re
import emoji

import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.join("GainzBot")
EQUIPMENT_FILE = os.path.join(BASE_DIR,"data/equipment.json")
HISTORY_FILE = os.path.join(BASE_DIR,"history/saved_workouts.json")

os.makedirs(os.path.dirname(EQUIPMENT_FILE),exist_ok=True)
os.makedirs(os.path.dirname(HISTORY_FILE),exist_ok=True)

class WorkoutApp(ctk.CTk):
    def __init__(self,llm_model="mistral-nemo"):
        super().__init__()
        self.llm_model = llm_model
        self.attributes("-topmost", True)
        self.title("G(ai)nzBot")
        self.geometry("1150x600")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar for equipment
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="nswe",pady=(30,5))
        self.sidebar.grid_rowconfigure(10, weight=1)
         
        ctk.CTkLabel(self.sidebar, text="Equipment", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,0))

        self.equipment_vars = {}
        self.load_equipment()

        self.equipment_scroll_container = ctk.CTkFrame(self.sidebar)
        self.equipment_scroll_container.pack(fill="both", expand=True, padx=10, pady=(20, 10))
 
        self.equipment_scroll_canvas = tk.Canvas(self.equipment_scroll_container, bg="#1e1e1e", highlightthickness=0)
        self.equipment_scrollbar = tk.Scrollbar(self.equipment_scroll_container, orient="vertical", command=self.equipment_scroll_canvas.yview)
        self.equipment_scroll_canvas.configure(yscrollcommand=self.equipment_scrollbar.set)
 
        self.equipment_scroll_canvas.pack(side="left", fill="both", expand=True)
        self.equipment_scrollbar.pack(side="right", fill="y")
 
        self.equipment_box_frame = ctk.CTkFrame(self.equipment_scroll_canvas)
        self.equipment_scroll_canvas.create_window((0, 0), window=self.equipment_box_frame, anchor="nw")
 
        self.equipment_box_frame.bind(
            "<Configure>",
            lambda e: self.equipment_scroll_canvas.configure(scrollregion=self.equipment_scroll_canvas.bbox("all"))
        )
 
        self.equipment_scroll_canvas.bind("<Enter>", lambda e: self.equipment_scroll_canvas.bind_all("<MouseWheel>", lambda ev: self.equipment_scroll_canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units")))
        self.equipment_scroll_canvas.bind("<Leave>", lambda e: self.equipment_scroll_canvas.unbind_all("<MouseWheel>"))

        self.update_equipment_checkboxes()

        # Main chat + workout area
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        self.chat_frame = ctk.CTkFrame(self.main_frame)
        self.chat_frame.grid(row=0, column=1, sticky="nswe", padx=(20, 20), pady=(0, 5))

        ctk.CTkLabel(self.chat_frame, text="Chat Display", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        self.chat_display = tk.Text(self.chat_frame, wrap="word", state="normal", height=30, width=60, bg="#1e1e1e", fg="white", insertbackground="white")
        self.chat_display.insert("0.0", "Welcome! How would you like to train today?")  # Placeholder text
        self.chat_display.configure(state="disabled")
        self.chat_display.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        self.chat_display.tag_config("bold", font=ctk.CTkFont(weight="bold"))
        self.create_model_selection_popup()

        # History frame
        self.history_frame = ctk.CTkFrame(self.main_frame)
        self.history_frame.grid(row=0, column=2, sticky="nswe", padx=(0, 20), pady=(0, 5))

        ctk.CTkLabel(self.history_frame, text="Workout History", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=1, padx=20, pady=(20, 10))
        self.history_display = tk.Text(self.history_frame, wrap="word", state="disabled", height=30, width=30, bg="#1e1e1e", fg="white", insertbackground="white")
        self.history_display.grid(row=1, column=1, rowspan=2, padx=(20, 5))

        self.history_up = ctk.CTkButton(self.history_frame, text="↑", width=30, command=self.scroll_workout_up)
        self.history_up.grid(row=1, column=2, pady=(0, 5))  # Up button in row 1

        self.history_down = ctk.CTkButton(self.history_frame, text="↓", width=30, command=self.scroll_workout_down)
        self.history_down.grid(row=2, column=2, pady=(5, 0))  # Down button in row 2

        # Configure grid row for spacing
        self.main_frame.grid_rowconfigure(2, weight=0)

        # Save button
        self.save_button = ctk.CTkButton(self.chat_frame, text="Save Workout", command=self.save_workout)
        self.save_button.grid(row=2, column=0, sticky="ne", padx=20, pady=(5, 10))

        # Input + send
        self.input_frame = ctk.CTkFrame(self.chat_frame)
        self.input_frame.grid(row=3, column=0, sticky="we", padx=20, pady=(0, 10))

        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Ask for a workout...")
        self.user_input.bind("<Return>", lambda event: self.send_button.invoke())
        self.user_input.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right")

        self.equipment_controls_frame = ctk.CTkFrame(self.sidebar)
        self.equipment_controls_frame.pack(pady=(10, 0), padx=20)

        self.new_equipment_entry = ctk.CTkEntry(self.equipment_controls_frame, placeholder_text="New equipment")
        self.new_equipment_entry.pack(pady=(10, 0), padx=20)
        self.new_equipment_entry.bind("<Return>", lambda event: self.add_equipment())

        self.add_eq_button = ctk.CTkButton(self.equipment_controls_frame, text="Add", command=self.add_equipment)
        self.add_eq_button.pack(pady=(5, 2), padx=20)

        self.messages = [{"role":"system","content":"""You are a GYM trainer, you should create workouts that fit the users request. 
                          Write the name of the exercises names, and the time/reptitions do to it.
                          Do not explain how to do the exercises unless asked todo so.
                          Summerize at the end of the workout which muscle groups it worked on and how much in percentage (adds up to 100%).
                          Use fun Emoji's.
                          
                          Look at the previous workouts the user did, generate an workout that complements the last one.
                          
                          Previous workouts
                          {}
                          """}]
        self.last_workout = ""
        self.history = []
        self.history_index = -1
        self.load_workout_history()

    def load_equipment(self):
        if os.path.exists(EQUIPMENT_FILE):
            with open(EQUIPMENT_FILE, "r") as f:
                saved = json.load(f)
                self.equipment_list = list(saved.keys())
                for eq, checked in saved.items():
                    self.equipment_vars[eq] = tk.BooleanVar(value=checked)
        else:
            self.equipment_list = ["Dumbbells", "Kettlebell", "Resistance Bands", "Pull-up Bar", "Jump Rope"]
            for eq in self.equipment_list:
                self.equipment_vars[eq] = tk.BooleanVar(value=False)
            self.save_equipment()

    def save_equipment(self):
        data = {eq: self.equipment_vars[eq].get() for eq in self.equipment_list}
        os.makedirs(os.path.dirname(EQUIPMENT_FILE), exist_ok=True)
        with open(EQUIPMENT_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def update_equipment_checkboxes(self):
        # Clear existing checkboxes
        for widget in self.equipment_box_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                widget.destroy()

        equip_copy = {k:v for k,v in self.equipment_vars.items()}
        # print(equip_copy)
        self.equipment_vars.clear()

        for eq in sorted(self.equipment_list,key=lambda x:x.lower()):
            var = ctk.BooleanVar(value=equip_copy[eq].get() if eq in equip_copy else False)
            row_frame = ctk.CTkFrame(self.equipment_box_frame)
            row_frame.pack(fill="x", padx=0, pady=2)

            chk = ctk.CTkCheckBox(row_frame, text=eq, variable=var, width=220)
            chk.pack(side="left", fill="x", expand=True, padx=(10, 5))
            
            # Bind checkbox state change to save equipment
            var.trace_add("write", lambda *args, eq=eq: self.save_equipment())

            del_btn = ctk.CTkButton(row_frame, text="-", width=30, command=lambda e=eq: self.remove_equipment_by_name(e))
            del_btn.pack(side="right", padx=(0, 10))

            self.equipment_vars[eq] = var
        

    def add_equipment(self):
        new_eq = self.new_equipment_entry.get().title()
        if new_eq and new_eq not in self.equipment_list:
            self.equipment_list.append(new_eq)
            self.update_equipment_checkboxes()
            self.sidebar.update()
            self.save_equipment()
            self.new_equipment_entry.delete(0, "end")

    def remove_equipment(self):
        eq_to_remove = self.new_equipment_entry.get()
        if eq_to_remove in self.equipment_list:
            self.equipment_list.remove(eq_to_remove)
            self.update_equipment_checkboxes()
            self.sidebar.update()
            self.save_equipment()

    def remove_equipment_by_name(self, equipment_name):
        if equipment_name in self.equipment_list:
            self.equipment_list.remove(equipment_name)
            self.update_equipment_checkboxes()
            self.sidebar.update()
            self.save_equipment()

    def create_model_selection_popup(self):
        self.model_list = [x['model'] for x in ollama.list()['models']]
        self.model_var = tk.StringVar(value=self.llm_model[:self.llm_model.find(':')])
        self.model_menu = tk.OptionMenu(self.chat_frame, self.model_var, *[x[:x.find(':')] for x in self.model_list], command=self.update_model)
        self.model_menu.config(width=15)
        self.model_menu.grid(row=2, column=0, sticky="nw", padx=20, pady=(5, 10))


    def update_model(self, selected_model):
            nn_model = ""
            for mod in self.model_list:
                if selected_model == mod[:len(selected_model)]:
                    nn_model = mod
                    break
            self.llm_model = nn_model

    def send_message(self):
        user_msg = self.user_input.get()
        if not user_msg:
            user_msg = "Generate a random workout based on past workouts"
        if user_msg:
            self.append_chat("\nYou", user_msg)
            self.chat_display.configure(state="normal")
            self.chat_display.insert("end", "\n")
            self.chat_display.configure(state="disabled")
            self.user_input.delete(0, 'end')

            selected_equipment = [eq for eq, var in self.equipment_vars.items() if var.get()]
            equipment_str = ", ".join(selected_equipment) if selected_equipment else "no equipment"

            self.messages.append({'role':'user','content': 
                f"Available Equipment for the workout:{equipment_str}\n{user_msg}"})
                        
            self.chat_display.configure(state="normal")
            
            # Remove the "typing..." text before streaming the actual response.
            # Assume the typing indicator is on the second-to-last line.
            typing_line_start = self.chat_display.index("end-2l linestart")
            typing_line_end = self.chat_display.index("end-2l lineend")
            self.chat_display.delete(typing_line_start, typing_line_end)
            # Reinsert "Coach: " at the beginning of that line
            self.chat_display.insert(typing_line_start, "Coach:\n", ("bold",))
            
            # Stream the response token-by-token
            workout_part = ""
            for chunk in ollama.chat(self.llm_model, messages=self.messages, stream=True,options={'num_ctx':4000}):
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    chunk_text = emoji.emojize(chunk.message.content, language='alias')
                    if not hasattr(self, "_bold_open"):
                        self._bold_open = False

                    parts = re.split(r"(\*\*)", chunk_text)
                    for part in parts:
                        if part == "**":
                            self._bold_open = not self._bold_open
                        else:
                            if self._bold_open:
                                self.chat_display.insert("end", part, ("bold",))
                            else:
                                self.chat_display.insert("end", part)
                            workout_part += part
                            self.chat_display.see("end")
                            self.update_idletasks()
                            self.chat_display.update()
            
            self.chat_display.insert("end", "\n")
            self.chat_display.configure(state="disabled")
            self.last_workout = workout_part  # Save the message for later

    def append_chat(self, sender, message):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}:", ("bold",))
        self.chat_display.insert("end", f" {message}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        

    def save_workout(self):
        if not self.last_workout:
            return  # Nothing to save

        workout_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "workout": self.last_workout,
            "equipment": [eq for eq, var in self.equipment_vars.items() if var.get()]
        }

        if os.path.exists(HISTORY_FILE):
            with open(save_path, "r") as f:
                all_workouts = json.load(f)
        else:
            all_workouts = []

        all_workouts.append(workout_data)

        with open(save_path, "w") as f:
            json.dump(all_workouts, f, indent=4)

        self.history = all_workouts
        self.history_index = len(self.history) - 1
        self.update_history_display()
        self.append_chat("System", "Workout saved! 💾")

    def load_workout_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(path, "r") as f:
                self.history = json.load(f)
            self.history_index = len(self.history) - 1
            self.update_history_display()
        
        
        workouts_hist = ""
        for hist_n in self.history:
            workouts_hist += f"{hist_n['date']}: {hist_n['workout']}"
        self.messages[0]['content'] = self.messages[0]['content'].format(workouts_hist)

    def update_history_display(self):
        self.history_display.configure(state="normal")
        self.history_display.delete("1.0", "end")
        if 0 <= self.history_index < len(self.history):
            entry = self.history[self.history_index]
            divider_width = int(self.history_display.cget("width")) // 1  # approx character width
            display_text = f"{entry['date']}\n" + "-" * divider_width + "\n" + entry["workout"]
            self.history_display.insert("end", display_text)
        self.history_display.configure(state="disabled")

    def scroll_workout_up(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.update_history_display()

    def scroll_workout_down(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.update_history_display()

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")  # You can change this
    app = WorkoutApp(
        llm_model="mistral-nemo"
        # llm_model="mistral-small:22b-instruct-2409-q3_K_L"
    )
    app.mainloop()