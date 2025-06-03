import tkinter as tk
import pickle
import os
import random
import numpy as np

POSE_POINTS_MAIN = {
    0: "cabeça",
    11: "ombro D",
    12: "ombro E",
    13: "cotovelo D",
    14: "cotovelo E",
    15: "mão D",
    16: "mão E",
    23: "cintura D",
    24: "cintura E"
}

POSE_CONNECTIONS = [
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 23), (12, 24),
    (23, 24)
]

GENERIC_POSE = {
    0: (300, 100),
    11: (250, 150), 12: (350, 150),
    13: (220, 200), 14: (380, 200),
    15: (200, 250), 16: (400, 250),
    23: (270, 250), 24: (330, 250),
}

num_variations = 20
noise_range = .02

def generate_variations(base_pose, num_variations, noise_range):
    variations = []
    for _ in range(num_variations):
        varied_pose = {}
        for idx, (x, y) in base_pose.items():
            dx = random.uniform(-noise_range, noise_range)
            dy = random.uniform(-noise_range, noise_range)
            varied_pose[idx] = (x + dx, y + dy)
        variations.append(varied_pose)
    return variations

def normalize_pose(pose):
    coords = np.array(list(pose.values()))
    center = np.mean(coords, axis=0)
    coords_centered = coords - center
    scale = np.max(np.linalg.norm(coords_centered, axis=1))
    if scale == 0:
        scale = 1
    coords_normalized = coords_centered / scale
    return {k: tuple(coords_normalized[i]) for i, k in enumerate(pose.keys())}

class PoseEditor:
    def __init__(self, master):
        self.master = master
        self.canvas_width = 600
        self.canvas_height = 300
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg='white')
        self.canvas.grid(row=0, column=0, rowspan=6, padx=10, pady=10)

        side_frame = tk.Frame(master)
        side_frame.grid(row=0, column=1, sticky="nw", padx=10, pady=10)

        tk.Label(side_frame, text="Nome da Pose:").pack(anchor="w")
        self.pose_name_var = tk.StringVar()
        self.entry_name = tk.Entry(side_frame, textvariable=self.pose_name_var)
        self.entry_name.pack(fill="x", pady=(0,10))

        tk.Label(side_frame, text="Mensagem MQTT:").pack(anchor="w")
        self.pose_msg_var = tk.StringVar()
        self.entry_msg = tk.Entry(side_frame, textvariable=self.pose_msg_var)
        self.entry_msg.pack(fill="x", pady=(0,10))


        tk.Button(side_frame, text="Salvar Pose", command=self.save_pose).pack(fill="x", pady=5)
        tk.Button(side_frame, text="Resetar Pose", command=self.reset_pose).pack(fill="x", pady=5)
        tk.Button(side_frame, text="Desfazer Último Movimento", command=self.undo).pack(fill="x", pady=5)
        tk.Button(side_frame, text="Remover Pose Selecionada", command=self.remove_selected_pose).pack(fill="x", pady=5)

        self.feedback_label = tk.Label(side_frame, text="", fg="green")
        self.feedback_label.pack(pady=(10,0))

        tk.Label(side_frame, text="Poses Salvas:").pack(anchor="w", pady=(20,0))
        self.listbox_poses = tk.Listbox(side_frame, height=10)
        self.listbox_poses.pack(fill="both", expand=True)
        self.listbox_poses.bind("<<ListboxSelect>>", self.load_selected_pose)

        self.points = {}
        self.labels = {}
        self.lines = []
        self.drag_data = {"item": None, "x": 0, "y": 0}

        self.history = []

        self.draw_pose()
        self.load_pose_names()

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

        self.canvas.tag_bind("draggable", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("draggable", "<Leave>", lambda e: self.canvas.config(cursor=""))

    def draw_pose(self):
        for idx, (x, y) in GENERIC_POSE.items():
            oval = self.canvas.create_oval(x-7, y-7, x+7, y+7, fill="blue", tags=("draggable", f"p{idx}"))
            self.points[idx] = oval
            label = self.canvas.create_text(x + 10, y - 10, text=POSE_POINTS_MAIN[idx], anchor="w", fill="black")
            self.labels[idx] = label
        self.draw_connections()

    def draw_connections(self):
        for line in self.lines:
            self.canvas.delete(line)
        self.lines.clear()
        for a, b in POSE_CONNECTIONS:
            if a in self.points and b in self.points:
                x1, y1, x2, y2 = self.canvas.coords(self.points[a])
                ax, ay = (x1 + x2) / 2, (y1 + y2) / 2
                x1, y1, x2, y2 = self.canvas.coords(self.points[b])
                bx, by = (x1 + x2) / 2, (y1 + y2) / 2
                line = self.canvas.create_line(ax, ay, bx, by, fill="gray", width=3)
                self.lines.append(line)

    def start_drag(self, event):
        item = self.canvas.find_withtag("current")
        if item:
            item = item[0]
            tags = self.canvas.gettags(item)
            if "draggable" in tags:
                self.drag_data["item"] = item
                self.drag_data["x"] = event.x
                self.drag_data["y"] = event.y
                self.save_current_state()
                self.canvas.itemconfig(item, fill="red")
            else:
                self.drag_data["item"] = None
        else:
            self.drag_data["item"] = None

    def drag(self, event):
        item = self.drag_data["item"]
        if item is None:
            return
        tags = self.canvas.gettags(item)
        if "draggable" not in tags:
            return

        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        x1, y1, x2, y2 = self.canvas.coords(item)
        new_x1 = x1 + dx
        new_y1 = y1 + dy
        new_x2 = x2 + dx
        new_y2 = y2 + dy

        if new_x1 < 0: dx = -x1
        if new_y1 < 0: dy = -y1
        if new_x2 > self.canvas_width: dx = self.canvas_width - x2
        if new_y2 > self.canvas_height: dy = self.canvas_height - y2

        self.canvas.move(item, dx, dy)
        for idx, oid in self.points.items():
            if oid == item:
                label_id = self.labels[idx]
                self.canvas.move(label_id, dx, dy)
                break

        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.draw_connections()

    def stop_drag(self, event):
        item = self.drag_data["item"]
        if item:
            self.canvas.itemconfig(item, fill="blue")
        self.drag_data["item"] = None

    def get_point_coords(self, idx):
        x1, y1, x2, y2 = self.canvas.coords(self.points[idx])
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def save_pose(self):
        pose_name = self.pose_name_var.get().strip()
        pose_msg = self.pose_msg_var.get().strip()
        if not pose_name:
            self.show_feedback("❌ Por favor, digite um nome para a pose.", "red")
            return
        if not pose_msg:
            self.show_feedback("❌ Por favor, digite uma mensagem MQTT.", "red")
            return


        base_pose = {}
        for idx, oid in self.points.items():
            x1, y1, x2, y2 = self.canvas.coords(oid)
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            base_pose[idx] = (x, y)

        pose_variations = generate_variations(base_pose, num_variations, noise_range)
        filename = "poses_salvas.pkl"

        if os.path.exists(filename):
            with open(filename, "rb") as f:
                all_poses = pickle.load(f)
        else:
            all_poses = {}

        normalized_variations = [normalize_pose(p) for p in pose_variations]
        all_poses[pose_name] = {
            "variations": normalized_variations,
            "message": pose_msg
        }

        with open(filename, "wb") as f:
            pickle.dump(all_poses, f)

        self.show_feedback("✅ Pose salva com sucesso!", "green")
        self.load_pose_names()

    def show_feedback(self, message, color):
        self.feedback_label.config(text=message, fg=color)
        self.master.after(3000, lambda: self.feedback_label.config(text=""))

    def reset_pose(self):
        self.save_current_state()
        for idx, (x, y) in GENERIC_POSE.items():
            oid = self.points[idx]
            x1, y1, x2, y2 = self.canvas.coords(oid)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            dx = x - cx
            dy = y - cy
            self.canvas.move(oid, dx, dy)
            label_id = self.labels[idx]
            self.canvas.move(label_id, dx, dy)
        self.draw_connections()
        self.show_feedback("Pose resetada.", "blue")

    def save_current_state(self):
        state = {}
        for idx, oid in self.points.items():
            x1, y1, x2, y2 = self.canvas.coords(oid)
            x, y = (x1 + x2) / 2, (y1 + y2) / 2
            state[idx] = (x, y)
        self.history.append(state)
        if len(self.history) > 20:
            self.history.pop(0)

    def undo(self):
        if not self.history:
            self.show_feedback("Nada para desfazer.", "orange")
            return
        last_state = self.history.pop()
        for idx, (x, y) in last_state.items():
            oid = self.points[idx]
            x1, y1, x2, y2 = self.canvas.coords(oid)
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            dx = x - cx
            dy = y - cy
            self.canvas.move(oid, dx, dy)
            label_id = self.labels[idx]
            self.canvas.move(label_id, dx, dy)
        self.draw_connections()
        self.show_feedback("Última ação desfeita.", "green")

    def load_pose_names(self):
        self.listbox_poses.delete(0, tk.END)
        filename = "poses_salvas.pkl"
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                all_poses = pickle.load(f)
            for name in sorted(all_poses.keys()):
                self.listbox_poses.insert(tk.END, name)

    def load_selected_pose(self, event):
        if not self.listbox_poses.curselection():
            return
        index = self.listbox_poses.curselection()[0]
        pose_name = self.listbox_poses.get(index)
        filename = "poses_salvas.pkl"
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                all_poses = pickle.load(f)
            if pose_name in all_poses:
                data = all_poses[pose_name]
                variations = data["variations"]
                msg = data.get("message", "")
                self.pose_msg_var.set(msg)

                avg_pose = {}
                for idx in GENERIC_POSE.keys():
                    xs = [p[idx][0] for p in variations]
                    ys = [p[idx][1] for p in variations]
                    avg_pose[idx] = (sum(xs)/len(xs), sum(ys)/len(ys))

                center_x, center_y = self.canvas_width / 2, self.canvas_height / 2
                scale = 150

                desnormalized_pose = {}
                for idx, (nx, ny) in avg_pose.items():
                    x = nx * scale + center_x
                    y = ny * scale + center_y
                    desnormalized_pose[idx] = (x, y)

                self.pose_name_var.set(pose_name)
                for idx, (x, y) in desnormalized_pose.items():
                    oid = self.points[idx]
                    x1, y1, x2, y2 = self.canvas.coords(oid)
                    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                    dx = x - cx
                    dy = y - cy
                    self.canvas.move(oid, dx, dy)
                    label_id = self.labels[idx]
                    self.canvas.move(label_id, dx, dy)
                self.draw_connections()
                self.show_feedback(f"Pose '{pose_name}' carregada.", "blue")
                self.history.clear()

    def remove_selected_pose(self):
        if not self.listbox_poses.curselection():
            self.show_feedback("Nenhuma pose selecionada.", "red")
            return
        index = self.listbox_poses.curselection()[0]
        pose_name = self.listbox_poses.get(index)

        filename = "poses_salvas.pkl"
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                all_poses = pickle.load(f)

            if pose_name in all_poses:
                del all_poses[pose_name]
                with open(filename, "wb") as f:
                    pickle.dump(all_poses, f)
                self.show_feedback(f"Pose '{pose_name}' removida.", "orange")
                self.load_pose_names()
                self.pose_name_var.set("")
            else:
                self.show_feedback("Erro ao remover pose.", "red")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Editor de Poses")
    app = PoseEditor(root)
    root.mainloop()