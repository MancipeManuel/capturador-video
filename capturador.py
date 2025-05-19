import cv2
import os
import csv
import numpy as np
from tkinter import Tk, filedialog, simpledialog, Button, Label, Frame
from PIL import Image, ImageTk
from datetime import datetime

# DPI estándar
DPI = 96

# Función para cargar y redimensionar imagen proporcionalmente
def cargar_imagen(path, ancho_max, alto_max):
    img = Image.open(path)
    img.thumbnail((ancho_max, alto_max), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

# Función para mostrar selector visual
def mostrar_selector_visual():
    root = Tk()
    root.title("Selector de estilo")
    root.geometry("600x500")
    root.resizable(False, False)
    selected_option = {"value": None}

    def seleccionar(opcion):
        selected_option["value"] = opcion
        root.quit()

    Label(root, text="Selecciona la imagen que más se parece al video que vas a procesar:").pack(pady=10)

    contenedor = Frame(root)
    contenedor.pack(pady=10)

    img1 = cargar_imagen("opcion1.png", 250, 350)
    btn1 = Button(contenedor, image=img1, command=lambda: seleccionar(1), borderwidth=2)
    btn1.image = img1
    btn1.grid(row=0, column=0, padx=20)

    img2 = cargar_imagen("opcion2.png", 250, 350)
    btn2 = Button(contenedor, image=img2, command=lambda: seleccionar(2), borderwidth=2)
    btn2.image = img2
    btn2.grid(row=0, column=1, padx=20)

    Label(contenedor, text="Estilo 1 (umbral 2)").grid(row=1, column=0, pady=5)
    Label(contenedor, text="Estilo 2 (umbral 14)").grid(row=1, column=1, pady=5)

    root.mainloop()
    root.destroy()
    return selected_option["value"]

# Selección de umbral
selected_option = mostrar_selector_visual()
if selected_option == 1:
    threshold = 2
elif selected_option == 2:
    threshold = 14
else:
    print("❌ No se seleccionó ninguna opción.")
    exit()

print(f"🔧 Umbral seleccionado: {threshold}")

# Ocultar ventana para el resto del flujo
root = Tk()
root.withdraw()

# Pedir nombre de carpeta de salida
output_folder = simpledialog.askstring(
    "Nombre de carpeta",
    "📁 Escribe el nombre de la carpeta donde se guardarán las capturas:"
)
if not output_folder:
    output_folder = "capturas_cambios"

# Pedir altura final del frame en centímetros y convertir a píxeles
alto_cm = simpledialog.askfloat(
    "Altura en centímetros",
    "📏 Escribe el alto (en cm) para las imágenes capturadas (ej: 10.0):",
    minvalue=1.0, maxvalue=50.0
)
if not alto_cm:
    alto_cm = 10.0

alto_final = int((alto_cm / 2.54) * DPI)
print(f"📐 Altura final: {alto_cm} cm → {alto_final} px")

# Carpeta con timestamp
timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
output_folder = f"{output_folder}_{timestamp_folder}"
os.makedirs(output_folder, exist_ok=True)
print(f"📁 Carpeta creada: {output_folder}")

# Selección de video
print("📂 Selecciona el archivo de video...")
video_path = filedialog.askopenfilename(
    title="Selecciona un video",
    filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv"), ("Todos los archivos", "*.*")]
)

if not video_path:
    print("❌ No se seleccionó ningún archivo.")
    exit()

video = cv2.VideoCapture(video_path)
if not video.isOpened():
    print("❌ No se pudo abrir el video.")
    exit()

fps = video.get(cv2.CAP_PROP_FPS)
if fps == 0:
    print("❌ FPS no detectado correctamente.")
    exit()

print(f"🎞️ FPS del video: {fps}")

ret, prev_frame = video.read()
if not ret:
    print("❌ No se pudo leer el primer frame.")
    exit()

prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
frame_count = 1
capture_count = 0

log_file = os.path.join(output_folder, "registro_capturas.csv")

# Crear CSV de registro
with open(log_file, mode='w', newline='') as log_csv:
    writer = csv.writer(log_csv)
    writer.writerow(["Captura", "Tiempo", "Frame", "Archivo"])

    print(f"\n📸 Detectando cambios en {os.path.basename(video_path)}...\n")

    while True:
        ret, frame = video.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_gray, gray)
        mean_diff = np.mean(diff)

        # Mostrar video en tiempo real
        preview_frame = cv2.resize(frame, (640, 360))
        cv2.imshow("Analizando video (presiona Q para salir)", preview_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("🚪 Salida anticipada por el usuario.")
            break

        if mean_diff > threshold:
            segundos = frame_count / fps
            minuto = int(segundos // 60)
            segundo = int(segundos % 60)
            tiempo = f"{minuto}:{segundo:02d}"
            nombre_archivo = f"cambio_{minuto} min {minuto}:{segundo:02d}".replace(":", "-") + ".jpg"

            alto_original, ancho_original = frame.shape[:2]
            escala = alto_final / alto_original
            ancho_final = int(ancho_original * escala)
            frame_redimensionado = cv2.resize(frame, (ancho_final, alto_final))

            filename = os.path.join(output_folder, nombre_archivo)
            cv2.imwrite(filename, frame_redimensionado)

            print(f"✅ Cambio detectado (frame {frame_count}, min {tiempo}) → {filename}")
            writer.writerow([capture_count, tiempo, frame_count, filename])
            capture_count += 1
            prev_gray = gray

        frame_count += 1

video.release()
cv2.destroyAllWindows()
print(f"\n🎉 Finalizado. Las capturas están en: {output_folder}")
print(f"📝 Registro de capturas: {log_file}")
