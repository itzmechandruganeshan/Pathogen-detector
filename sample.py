import os
import tkinter as tk
from tkinter import filedialog, scrolledtext

class ProjectStructure:
    def __init__(self, startpath, ignore_dirs=None, ignore_files=None):
        self.startpath = startpath
        self.ignore_dirs = ignore_dirs if ignore_dirs is not None else ['.git', '__pycache__', 'node_modules']
        self.ignore_files = ignore_files if ignore_files is not None else ['*.pyc', '*.log', '*.tmp', '*.swp']

    def list_files(self):
        file_tree = []
        try:
            for root, dirs, files in os.walk(self.startpath):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                # Filter out ignored files
                files = [f for f in files if not any(f.endswith(ext) for ext in self.ignore_files)]

                level = root.replace(self.startpath, '').count(os.sep)
                indent = ' ' * 4 * level
                file_tree.append(f'{indent}{os.path.basename(root)}/')
                subindent = ' ' * 4 * (level + 1)
                for f in files:
                    file_tree.append(f'{subindent}{f}')
        except Exception as e:
            file_tree.append(f"Error occurred: {e}")
        return "\n".join(file_tree)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Folder Structure")
        self.root.attributes('-fullscreen', True)  # Open in full screen
        
        # Disable default close button
        self.root.protocol("WM_DELETE_WINDOW", self.disable_close)
        
        # Decorative background
        self.bg_color = "#f0f8ff"
        self.root.configure(bg=self.bg_color)
        
        # Apply a custom font and styling
        self.font = ('Arial', 12)
        self.create_widgets()

    def create_widgets(self):
        # Custom title bar
        self.title_bar = tk.Frame(self.root, bg="#4682b4", relief="raised", bd=2)
        self.title_bar.pack(fill=tk.X)

        # Minimize, Maximize, Close buttons
        self.minimize_button = tk.Button(self.title_bar, text="_", command=self.minimize_window, bg="#87cefa", fg="black", font=self.font)
        self.minimize_button.pack(side=tk.LEFT, padx=5)
        
        self.maximize_button = tk.Button(self.title_bar, text="☐", command=self.maximize_window, bg="#87cefa", fg="black", font=self.font)
        self.maximize_button.pack(side=tk.LEFT, padx=5)
        
        self.close_button = tk.Button(self.title_bar, text="X", command=self.close_window, bg="#ff6347", fg="black", font=self.font)
        self.close_button.pack(side=tk.RIGHT, padx=5)
        
        # Path entry
        self.path_label = tk.Label(self.root, text="Select Project Folder:", bg=self.bg_color, font=self.font, padx=10, pady=5)
        self.path_label.pack(pady=10)

        self.path_entry = tk.Entry(self.root, width=60, font=self.font)
        self.path_entry.pack(pady=5)

        self.browse_button = tk.Button(self.root, text="Browse", command=self.browse_folder, font=self.font, bg="#87cefa", fg="black")
        self.browse_button.pack(pady=5)

        self.show_button = tk.Button(self.root, text="Show Structure", command=self.show_structure, font=self.font, bg="#87cefa", fg="black")
        self.show_button.pack(pady=10)

        # Text area to show file structure
        self.text_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, width=80, font=self.font, bg="#ffffff", fg="black")
        self.text_area.pack(pady=10, padx=10)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)

    def show_structure(self):
        path = self.path_entry.get()
        if os.path.isdir(path):
            project_structure = ProjectStructure(path)
            structure = project_structure.list_files()
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, structure)
        else:
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, "Invalid directory path.")
    
    def disable_close(self):
        pass  # Do nothing on close attempt

    def minimize_window(self):
        self.root.iconify()

    def maximize_window(self):
        self.root.attributes('-fullscreen', not self.root.attributes('-fullscreen'))

    def close_window(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()