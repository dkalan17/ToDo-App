import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from gpt4all import GPT4All  # pip install gpt4all

class ToDoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List")
        self.root.geometry("400x650+400+100")
        self.root.resizable(True, True)  # allow window resizing

        # Holds all main tasks and subtasks
        self.task_groups = []

        # >>> Set your GPT4All .bin model path here <<<
        self.gpt4all_model_path = "mistral-7b-instruct-v0.1.Q4_0.gguf"

        # Attempt to load GPT4All model
        try:
            self.gpt_model = GPT4All(self.gpt4all_model_path)
        except Exception as e:
            messagebox.showerror("GPT4All Error", f"Could not load GPT4All model: {e}")
            self.gpt_model = None

        self.load_images()
        self.create_ui()
        self.load_tasks()

    def load_images(self):
        """
        Load and store your images here.
        Change the paths as needed for your environment.
        """
        img_dir = "IMAGES/"
        self.images = {
            "icon": self.load_image(os.path.join(img_dir, "checklist.png"), (40, 40)),
            "top_bar": self.load_image(os.path.join(img_dir, "top_bar.png"), (2000, 75)),
            "dock": self.load_image(os.path.join(img_dir, "dock.png"), (40, 40))
        }

    def load_image(self, path, size):
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)

    def create_ui(self):
        # Header frame: fixed height, fills the width
        header_frame = tk.Frame(self.root, bg="#545454")
        header_frame.place(relx=0, rely=0, relwidth=1, height=75)
        # Top bar image (stays centered horizontally)
        tk.Label(header_frame, image=self.images["top_bar"]).pack(fill="both", expand=True)
        # Overlay the icon and title text using relative coordinates
        tk.Label(header_frame, image=self.images["icon"], bg="#545454")\
            .place(relx=0.9, rely=0.5, anchor="center")
        tk.Label(header_frame, text="Don't Give Up", font="Consolas 20 bold",
                 fg="white", bg="#545454")\
            .place(relx=0.4875, rely=0.5, anchor="center")

        # Frame for the task entry
        # Original fixed coordinates (x=0, y=180, width=400, height=50) translate roughly to:
        # relx=0, rely ~0.28, relwidth=1, and a fixed height
        task_entry_frame = tk.Frame(self.root, bg="white")
        task_entry_frame.place(relx=0, rely=0.28, relwidth=1, height=50)
        self.task_var = tk.StringVar()
        # Position the entry to take about 65% of the frame width
        self.task_entry = tk.Entry(task_entry_frame, font="Consolas 20", bd=0, textvariable=self.task_var)
        self.task_entry.place(relx=0.025, rely=0.14, relwidth=0.65, relheight=0.7)
        self.task_entry.bind("<Return>", lambda event: self.add_task())
        # ADD button fills the remaining width (about 18% of the frame width)
        self.add_button = tk.Button(task_entry_frame, text="ADD", font="Consolas 20", bd=0, bg="#d3d3d3",
                                    command=self.add_task)
        self.add_button.place(relx=0.8, rely=0, relwidth=0.18, relheight=1)

        # Scrollable task list
        # Original fixed values (x=10, y=250, width=380, height=330) translate roughly to:
        # relx ~0.025, rely ~0.3846, relwidth ~0.95, relheight ~0.5077
        self.task_frame = tk.Frame(self.root)
        self.task_frame.place(relx=0.025, rely=0.3846, relwidth=0.95, relheight=0.5077)
        self.canvas = tk.Canvas(self.task_frame)
        self.scrollbar = tk.Scrollbar(self.task_frame, orient="vertical", command=self.canvas.yview)
        self.tasks_container = tk.Frame(self.canvas)
        self.tasks_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.tasks_container, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mouse wheel scrolling
        def on_mouse_wheel(event):
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        self.canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", on_mouse_wheel)  # Linux Scroll Up
        self.canvas.bind_all("<Button-5>", on_mouse_wheel)  # Linux Scroll Down

        # Delete button: centered near the bottom of the window
        delete_button = tk.Button(self.root, text="DELETE", font="Consolas 15", bg="red", fg="white",
                                  command=self.delete_task)
        delete_button.place(relx=0.5, rely=0.92, anchor="center")

    def add_task(self):
        """Add a new main task and its subtasks."""
        task = self.task_var.get().strip()
        if task:
            subtasks = self.generate_subtasks(task)
            main_var = tk.IntVar()
            main_chk = tk.Checkbutton(self.tasks_container, text=task, font="Consolas 15", variable=main_var)
            main_chk.pack(anchor="w", padx=5, pady=2)
            subtask_widgets = []
            for sub in subtasks:
                sub_var = tk.IntVar()
                sub_chk = tk.Checkbutton(self.tasks_container, text="  - " + sub, font="Consolas 13", variable=sub_var)
                sub_chk.pack(anchor="w", padx=20, pady=1)
                subtask_widgets.append((sub_chk, sub_var))
            self.task_groups.append({"main": (main_chk, main_var, task), "subtasks": subtask_widgets})
            self.task_var.set("")
            self.save_tasks()
        else:
            messagebox.showwarning("Warning", "Task cannot be empty!")

    def delete_task(self):
        """Delete all main tasks that are checked (along with their subtasks)."""
        self.root.update_idletasks()
        groups_to_keep = []
        for group in self.task_groups:
            main_chk, main_var, task_text = group["main"]
            if main_var.get() == 1:
                main_chk.destroy()
                for sub_chk, _ in group["subtasks"]:
                    sub_chk.destroy()
            else:
                groups_to_keep.append(group)
        self.task_groups = groups_to_keep
        self.save_tasks()

    def save_tasks(self):
        """Save only the main tasks to a text file (subtasks are re-generated)."""
        with open("tasks.txt", "w") as file:
            for group in self.task_groups:
                main_chk, main_var, task_text = group["main"]
                file.write(task_text + "\n")

    def load_tasks(self):
        """Load tasks from 'tasks.txt' and re-generate their subtasks."""
        if os.path.exists("tasks.txt"):
            with open("tasks.txt", "r") as file:
                for line in file:
                    task = line.strip()
                    if task:
                        self.task_var.set(task)
                        self.add_task()

    def generate_subtasks(self, task):
        """
        Ask GPT4All to break the main task into 3 subtasks.
        If GPT4All isn't loaded or fails, fallback to default subtasks.
        """
        prompt = (f"Your task is to break down a given task into three smaller, actionable subtasks. Each subtask should be no longer than 3 words and should be clear, specific, and easy to execute. Here is the task: {task}. Provide the subtasks in a numbered list.")
        try:
            if self.gpt_model:
                response = self.gpt_model.generate(prompt)
                subtasks = response.strip().split("\n")
                subtasks = [sub.strip("- ").strip() for sub in subtasks if sub.strip()]
                if len(subtasks) < 3:
                    subtasks += ["Subtask 1", "Subtask 2", "Subtask 3"][len(subtasks):]
                return subtasks[:3]
            else:
                raise Exception("GPT4All model not loaded.")
        except Exception as e:
            print(f"Error generating subtasks: {e}")
            return ["Subtask 1", "Subtask 2", "Subtask 3"]

if __name__ == "__main__":
    root = tk.Tk()
    app = ToDoApp(root)
    root.mainloop()