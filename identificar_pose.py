import tkinter as tk
import cv2
import mediapipe as mp
import numpy as np
import pickle
import paho.mqtt.client as mqtt

broker = "broker.hivemq.com"
port = 1883
topic = "GS/3ESA/iot"
client = mqtt.Client(protocol=mqtt.MQTTv311)
client.connect(broker, port, 60)


POINTS_USED = [11, 12, 13, 14, 15, 16, 23, 24]
POSE_FILE = "poses_salvas.pkl"

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_draw = mp.solutions.drawing_utils

def normalize_pose(pose):
    coords = np.array(list(pose.values()))
    center = np.mean(coords, axis=0)
    coords_centered = coords - center
    scale = np.max(np.linalg.norm(coords_centered, axis=1))
    if scale == 0:
        scale = 1
    coords_normalized = coords_centered / scale
    return {k: tuple(coords_normalized[i]) for i, k in enumerate(pose.keys())}

def compare_poses(p1, p2):
    total = 0
    for k in p1:
        if k in p2:
            total += np.linalg.norm(np.array(p1[k]) - np.array(p2[k]))
    return total

with open(POSE_FILE, "rb") as f:
    raw_poses = pickle.load(f)

normalized_poses = {}
pose_messages = {}

for name, data in raw_poses.items():
    variations = data["variations"] if isinstance(data, dict) else data
    normalized_poses[name] = [normalize_pose(p) for p in variations]
    if isinstance(data, dict) and "message" in data:
        pose_messages[name] = data["message"]


def process_frame(frame, threshold):
    mensagem = ""
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark
        points = {i: (landmarks[i].x, landmarks[i].y) for i in POINTS_USED}
        input_pose = normalize_pose(points)

        distances = []
        for name, variations in normalized_poses.items():
            dists = [compare_poses(input_pose, var) for var in variations]
            min_dist = min(dists)
            distances.append((name, min_dist))

        distances.sort(key=lambda x: x[1])
        best_pose = distances[0]

        if best_pose[1] < threshold:
            main_label = f"✅ Pose: {best_pose[0]} ({best_pose[1]:.2f})"
            color = (0, 255, 0)
            mensagem = pose_messages.get(best_pose[0], f"Pose: {best_pose[0]}")
            client.publish(topic, mensagem)

        else:
            main_label = "❌ Nenhuma pose reconhecida"
            color = (0, 0, 255)

        cv2.putText(frame, main_label, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    return frame


def run_pose_detection():
    threshold = slider.get()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro ao abrir webcam.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        processed = process_frame(frame, threshold)
        cv2.imshow("Reconhecimento de Pose (Webcam)", processed)
        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


root = tk.Tk()
root.title("Reconhecimento de Pose - Normalizado")

tk.Label(root, text="Tolerância:").pack()
slider = tk.Scale(root, from_=1, to=10, resolution=0.5, orient="horizontal")
slider.set(1)
slider.pack()

tk.Button(root, text="Iniciar com Webcam", command=run_pose_detection).pack(pady=10)

root.mainloop()
