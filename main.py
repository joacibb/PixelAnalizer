import tkinter as tk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
import numpy as np


class ImageViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Visor de Imágenes por Joaquín Cibanal")
        self.root.geometry("1360x768")  # Establecer el tamaño fijo de la ventana

        self.show_full_image = True  # Inicializar la variable de control
        self.show_filtered_image = False

        self.button_bar = tk.Frame(root, bg="lightgray")
        self.button_bar.pack(side=tk.TOP, fill=tk.X)

        self.load_button = tk.Button(self.button_bar, text="Cargar Imagen", command=self.load_image)
        self.load_button.pack(side=tk.LEFT)

        self.calculate_button = tk.Button(self.button_bar, text="Calcular Porcentajes", command=self.calculate_percentages)
        self.calculate_button.pack(side=tk.LEFT)

        self.result_label = tk.Label(root, text="", bg="lightgray")
        self.result_label.pack(side=tk.BOTTOM, fill=tk.X)

        self.show_red_button = tk.Button(self.button_bar, text="Mostrar Rojos", command=self.show_red_pixels)
        self.show_red_button.pack(side=tk.LEFT)

        self.image_frame = tk.Frame(root, bg="black")
        self.image_frame.pack(expand=True, fill=tk.BOTH)

        self.label = tk.Label(self.image_frame)
        self.label.pack(expand=True)

        self.image = None
        self.original_image = None
        self.zoom_factor = 1.0
        self.zoom_position = (0, 0)

        self.image_position = (0, 0)
        self.drag_start = None

        self.reset_button = tk.Button(self.button_bar, text="Restablecer Imagen", command=self.reset_image)
        self.reset_button.pack(side=tk.LEFT)

        # Deshabilitar los botones excepto el de "Cargar Imagen"
        self.calculate_button.config(state=tk.DISABLED)
        self.show_red_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.DISABLED)

        self.label.bind("<Button-1>", self.on_drag_start)
        self.label.bind("<B1-Motion>", self.on_drag_motion)
        self.label.bind("<ButtonRelease-1>", self.on_drag_release)
        self.label.bind("<MouseWheel>", self.on_mouse_wheel)

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = cv2.imread(file_path)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.image = Image.fromarray(self.image)
            self.original_image = self.image.copy()

            # Calcular la posición inicial para centrar la imagen en el centro de la ventana
            window_width = self.root.winfo_width()  # Obtener el ancho de la ventana
            window_height = self.root.winfo_height()  # Obtener la altura de la ventana
            image_width, image_height = self.original_image.size

            initial_x = (window_width - image_width) / 2
            initial_y = (window_height - image_height) / 2

            self.image_position = (initial_x, initial_y)  # Establecer la posición inicial
            self.zoom_factor = 1.0  # Restablecer el zoom
            self.show_filtered_image = False  # Cambiar el valor de la variable de control

            self.update_display()  # Mostrar la imagen centrada en la ventana

            # Habilitar los botones después de cargar la imagen
            self.calculate_button.config(state=tk.NORMAL)
            self.show_red_button.config(state=tk.NORMAL)
            self.reset_button.config(state=tk.NORMAL)

    def on_drag_start(self, event):
        self.drag_start = (event.x, event.y)

    def on_drag_motion(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.image_position = (self.image_position[0] - dx, self.image_position[1] - dy)
            self.drag_start = (event.x, event.y)
            self.update_display()

    def on_drag_release(self, event):
        self.drag_start = None

    def on_click(self, event):
        if hasattr(self, 'image'):
            self.image_position = (event.x, event.y)
            self.update_display()

    def on_mouse_wheel(self, event):
        if hasattr(self, 'image'):
            zoom_factor_change = 1.1 ** (event.delta / 120.0)
            self.zoom_factor *= zoom_factor_change
            self.update_display()

    def show_red_pixels(self):
        if hasattr(self, 'original_image'):
            self.show_filtered_image = True
            self.update_display()
            image_np = np.array(self.image)
            hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

            lower_red = np.array([0, 100, 100])  # Rango mínimo para el rojo en HSV
            upper_red = np.array([12, 255, 255])  # Rango máximo para el rojo en HSV

            mask = cv2.inRange(hsv_image, lower_red, upper_red)
            red_pixels = cv2.bitwise_and(image_np, image_np, mask=mask)

            red_image = Image.fromarray(red_pixels)
            self.image = red_image  # Actualizar la referencia a la imagen filtrada
            self.show_full_image = False  # Cambiar el valor de la variable de control
            self.update_display()  # Actualizar la visualización con la imagen filtrada

    def reset_image(self):
        if hasattr(self, 'original_image'):
            self.image = self.original_image.copy()  # Restaurar la referencia a la imagen original
            self.image_position = (0, 0)  # Resetear la posición
            self.zoom_factor = 1.0  # Resetear el zoom
            self.show_filtered_image = False  # Cambiar el valor de la variable de control
            self.update_display()  # Actualizar la visualización con la imagen original

    def update_display(self):
        if hasattr(self, 'image'):
            x, y = self.image_position
            if self.show_filtered_image:
                zoomed_image = self.image  # Mostrar la imagen filtrada
            else:
                zoomed_image = self.zoom_at(self.original_image, x, y, self.zoom_factor)

            self.image_tk = ImageTk.PhotoImage(zoomed_image)
            self.label.config(image=self.image_tk)
            self.label.image = self.image_tk

    def zoom_in(self, event):
        if hasattr(self, 'image'):
            self.zoom_factor *= 1.1
            self.zoom_position = (event.x, event.y)
            self.update_display()

    def zoom_out(self, event):
        if hasattr(self, 'image'):
            self.zoom_factor /= 1.1
            self.zoom_position = (event.x, event.y)
            self.update_display()

    def zoom_at(self, img, x, y, zoom):
        w, h = img.size
        zoom2 = zoom * 2
        img = img.crop((x - w / zoom2, y - h / zoom2,
                        x + w / zoom2, y + h / zoom2))
        return img.resize((w, h), Image.LANCZOS)

    def calculate_percentages(self):
        if hasattr(self, 'image'):
            image_np = np.array(self.image)
            rgb_image = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
            hsv_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)

            non_black_pixels = np.any(rgb_image != [0, 0, 0], axis=-1)

            # Calcular los porcentajes para cada color
            total_area = np.sum(non_black_pixels)

            # Umbral para píxeles rojos (Hue en HSV)
            red_hue_lower = 0  # Matiz mínimo para el rojo
            red_hue_upper = 10  # Matiz máximo para el rojo
            is_red_hue = np.logical_or(hsv_image[..., 0] <= red_hue_upper, hsv_image[..., 0] >= red_hue_lower)

            # Umbral para píxeles amarillos (Hue en HSV)
            yellow_hue_lower = 25  # Ampliar el rango para amarillo
            yellow_hue_upper = 35
            is_yellow_hue = (hsv_image[..., 0] >= yellow_hue_lower) & (hsv_image[..., 0] <= yellow_hue_upper)

            # Umbral para píxeles verdes (Hue en HSV)
            green_hue_lower = 40
            green_hue_upper = 80
            is_green_hue = (hsv_image[..., 0] >= green_hue_lower) & (hsv_image[..., 0] <= green_hue_upper)

            # Umbral para píxeles azules (Hue en HSV)
            blue_hue_lower = 100
            blue_hue_upper = 140
            is_blue_hue = (hsv_image[..., 0] >= blue_hue_lower) & (hsv_image[..., 0] <= blue_hue_upper)

            # Umbral para píxeles de saturación alta (Saturation en HSV)
            high_saturation_threshold = 100  # Umbral de saturación alta
            is_high_saturation = hsv_image[..., 1] >= high_saturation_threshold

            # Combinar los umbrales de matiz y saturación para detectar píxeles de diferentes colores
            is_red = is_red_hue & is_high_saturation
            is_yellow = is_yellow_hue & is_high_saturation
            is_green = is_green_hue & is_high_saturation
            is_blue = is_blue_hue & is_high_saturation

            # Calcular los porcentajes para cada color
            red_percentage = ((np.sum(is_red) - np.sum(is_yellow)) / total_area) * 100
            yellow_percentage = (np.sum(is_yellow) / total_area) * 100
            green_percentage = (np.sum(is_green) / total_area) * 100
            blue_percentage = (np.sum(is_blue) / total_area) * 100

            result_text = (
                f"Porcentaje de Áreas Rojas: {red_percentage:.2f}%\n"
                f"Porcentaje de Áreas Amarillas: {yellow_percentage:.2f}%\n"
                f"Porcentaje de Áreas Verdes: {green_percentage:.2f}%\n"
                f"Porcentaje de Áreas Azules: {blue_percentage:.2f}%\n"
            )

            self.result_label.config(text=result_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageViewerApp(root)
    root.mainloop()
