import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import math
from ultralytics import YOLO


class PeopleCounter:
    """Подсчет людей с веб-камеры с помощью YOLO и проверки пересечения линии."""
    def __init__(self, root):
        self.root = root
        self.root.title("Система подсчета людей")

        self.model = None

        with open("coco.names", "r") as f:
            self.classes = f.read().strip().split("\n")

        # Счетчик людей, находящихся внутри помещения
        # Будет увеличиваться, когда люди пересекают линию в одном направлении
        # и уменьшаться - в другом
        self.people_inside = 0

        # Словарь для хранения предыдущих позиций людей
        # Ключ - ID человека, значение - его координаты
        # Нужен для определения, пересек ли человек линию
        self.previous_positions = {}

        # Флаг, показывающий, находимся ли мы в режиме настройки линии
        # True - можно настраивать линию, False - идет подсчет людей
        self.setup_mode = True

        self.setup_ui()

        # Инициализируем камеру (0 - обычно встроенная камера ноутбука)
        # На Windows ускоряет открытие: CAP_DSHOW
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
        except Exception:
            self.cap = cv2.VideoCapture(0)
        # Уменьшаем задержки буфера и ставим пониженное разрешение
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
        # Устанавливаем пониженное разрешение камеры для лучшей производительности
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)  # Ширина кадра
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)  # Высота кадра

        # Запускаем предварительный просмотр для настройки линии
        self.setup_preview()

    def setup_ui(self):
        # Создаем основную рамку для отображения видео
        self.video_frame = ttk.Frame(self.root)
        # Размещаем рамку с отступом сверху и снизу 10 пикселей
        self.video_frame.pack(pady=10)

        # Создаем метку (label) внутри video_frame, где будет показываться видео с камеры
        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack()

        # Создаем рамку для элементов управления (слайдеры и кнопка)
        self.control_frame = ttk.Frame(self.root)
        # Размещаем её с отступом 10 пикселей
        self.control_frame.pack(pady=10)

        # Создаем отдельную рамку для слайдеров
        self.sliders_frame = ttk.Frame(self.control_frame)
        # Размещаем слайдеры слева с отступом 10 пикселей
        self.sliders_frame.pack(side=tk.LEFT, padx=10)

        # Создаем подпись для первого слайдера
        ttk.Label(self.sliders_frame, text="Положение линии:").pack()
        # Создаем слайдер для регулировки вертикального положения линии
        self.line_position = tk.Scale(
            self.sliders_frame,  # Родительский элемент - рамка слайдеров
            from_=0,  # Минимальное значение слайдера
            to=100,  # Максимальное значение слайдера
            orient=tk.HORIZONTAL,  # Горизонтальная ориентация слайдера
            length=200,  # Длина слайдера в пикселях
        )
        # Устанавливаем начальное положение слайдера на середину (50%)
        self.line_position.set(50)
        self.line_position.pack()

        # Создаем подпись для второго слайдера
        ttk.Label(self.sliders_frame, text="Угол поворота (градусы):").pack()
        # Создаем слайдер для регулировки угла наклона линии
        self.line_angle = tk.Scale(
            self.sliders_frame,  # Родительский элемент - рамка слайдеров
            from_=0,  # Минимальный угол - 0 градусов
            to=359,  # Максимальный угол - 359 градусов
            orient=tk.HORIZONTAL,  # Горизонтальная ориентация слайдера
            length=200,  # Длина слайдера в пикселях
        )
        # Устанавливаем начальный угол 0 градусов (горизонтальная линия)
        self.line_angle.set(0)
        self.line_angle.pack()

        # Создаем кнопку для начала подсчета людей
        self.start_button = ttk.Button(
            self.control_frame,  # Родительский элемент - рамка управления
            text="Начать подсчет",  # Текст на кнопке
            command=self.start_counting,  # Функция, которая вызывается при нажатии
        )
        # Размещаем кнопку справа от слайдеров с отступом 20 пикселей
        self.start_button.pack(side=tk.LEFT, padx=20)

        # Создаем рамку для отображения счетчика людей (изначально скрыта)
        self.counter_frame = ttk.Frame(self.root)

        # Создаем метку для отображения количества людей
        self.count_label = ttk.Label(
            self.counter_frame,  # Родительский элемент - рамка счетчика
            text="Людей в помещении: 0",  # Начальный текст
            font=("Helvetica", 16, "bold"),  # Настройки шрифта
        )
        # Размещаем метку с отступом 10 пикселей по горизонтали
        self.count_label.pack(padx=10)

    def get_line_points(self, frame_width, frame_height):
        """Вычисляет координаты начала и конца линии подсчета с учетом соотношения сторон кадра"""
        # Центр кадра
        center_x = frame_width // 2
        center_y = frame_height // 2

        # Получаем угол и переводим в радианы
        angle = self.line_angle.get()
        angle_rad = math.radians(angle)

        # Вычисляем коэффициент масштабирования смещения в зависимости от угла
        # При 0° и 180° (горизонтальная линия) используем высоту кадра
        # При 90° и 270° (вертикальная линия) используем ширину кадра
        # Между ними - плавный переход
        vertical_factor = abs(math.sin(angle_rad))
        horizontal_factor = abs(math.cos(angle_rad))

        max_offset = max(frame_width, frame_height)

        # Вычисляем смещение с учетом угла наклона
        base_offset = (self.line_position.get() - 50) / 50.0  # От -1 до 1
        offset_x = base_offset * frame_width * vertical_factor
        offset_y = base_offset * frame_height * horizontal_factor

        # Используем длину, гарантирующую пересечение кадра при любом угле
        line_length = math.sqrt(frame_width**2 + frame_height**2) * 1.5
        half_length = line_length / 2

        # Вычисляем базовые точки линии
        x1 = center_x + half_length * math.cos(angle_rad)
        y1 = center_y + half_length * math.sin(angle_rad)
        x2 = center_x - half_length * math.cos(angle_rad)
        y2 = center_y - half_length * math.sin(angle_rad)

        # Применяем смещение в зависимости от угла
        x1 += offset_x
        x2 += offset_x
        y1 += offset_y
        y2 += offset_y

        return (int(x1), int(y1)), (int(x2), int(y2))

    def point_position_relative_to_line(self, point, line_start, line_end):
        """Определяет, с какой стороны от линии находится точка

        Использует векторное произведение для определения положения точки:
        - Если результат > 0, точка находится с одной стороны линии
        - Если результат < 0, точка находится с другой стороны
        - Если результат = 0, точка лежит на линии
        """
        # Получаем координаты проверяемой точки
        x, y = point
        # Получаем координаты начала линии
        x1, y1 = line_start
        # Получаем координаты конца линии
        x2, y2 = line_end

        # Вычисляем векторное произведение
        # (x2-x1)(y-y1) - (y2-y1)(x-x1)
        # Это определяет, с какой стороны от линии находится точка
        return (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)

    def get_optimized_frame(self):
        """Читает кадр, делает горизонтальное зеркало и возвращает копию для рисования."""
        # Читаем кадр с камеры
        # ret - успешность получения кадра (True/False)
        # frame - сам кадр в формате numpy array
        ret, frame = self.cap.read()

        if ret:  # Если кадр успешно получен
            # Отражаем кадр по горизонтали для естественного отображения
            # (чтобы движения соответствовали реальным)
            frame = cv2.flip(frame, 1)

            # Создаем копию кадра для отображения
            # (чтобы рисование на нем не влияло на обработку)
            display_frame = frame.copy()

            return True, frame, display_frame
        return False, None, None

    def detect_people(self, frame):
        """Возвращает список `[x1, y1, x2, y2]` детекций класса person на кадре."""
        # Ленивая загрузка модели при первом обращении в режиме подсчета
        if self.model is None:
            self.model = YOLO("yolov8n.pt")

        # Запускаем YOLO для обнаружения только класса 'person' (индекс 0)
        # Уменьшаем порог NMS для лучшего разделения близко стоящих людей
        # Увеличиваем conf для уменьшения ложных срабатываний
        results = self.model(
            frame,
            classes=0,
            conf=0.35,  # Снижаем порог уверенности для обнаружения
            iou=0.3,    # Уменьшаем IoU для лучшего разделения близких объектов
            max_det=10  # Увеличиваем максимальное количество детекций
        )

        # Список для хранения координат обнаруженных людей
        boxes = []

        # Обрабатываем результаты детекции
        for result in results:
            # Перебираем все найденные объекты
            for box in result.boxes:
                # Получаем координаты рамки из результатов YOLO
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())

                # Фильтруем по размеру рамки, чтобы исключить слишком маленькие детекции
                box_width = x2 - x1
                box_height = y2 - y1
                min_size = 30  # Минимальный размер рамки в пикселях

                if box_width > min_size and box_height > min_size:
                    # Преобразуем координаты в целые числа и добавляем в список
                    boxes.append([int(x1), int(y1), int(x2), int(y2)])

        return boxes

    def setup_preview(self):
        """Предпросмотр с линией для режима настройки."""
        ret, _, display_frame = self.get_optimized_frame()
        if ret:
            # Получаем точки линии
            line_start, line_end = self.get_line_points(
                display_frame.shape[1], display_frame.shape[0]
            )

            # Рисуем линию
            cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

            # Конвертируем кадр для отображения в tkinter
            img = Image.fromarray(display_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        if self.setup_mode:
            self.root.after(30, self.setup_preview)

    def check_line_crossing(self, current_pos, previous_pos, line_start, line_end):
        """Проверяет факт пересечения линии и определяет направление (in/out)."""
        # Если нет предыдущей позиции, пересечения быть не может
        if previous_pos is None:
            return False, None

        # Определяем, с какой стороны линии находилась предыдущая позиция
        prev_side = self.point_position_relative_to_line(
            previous_pos, line_start, line_end
        )
        # Определяем, с какой стороны линии находится текущая позиция
        curr_side = self.point_position_relative_to_line(
            current_pos, line_start, line_end
        )

        # Если знаки разные (произведение < 0), значит линия была пересечена
        if (prev_side * curr_side) < 0:
            # Получаем текущий угол линии для определения направления
            angle = self.line_angle.get()

            # В зависимости от угла наклона линии определяем направление
            # Для углов 0-179 градусов:
            #   - если prev_side > 0, человек двигается внутрь
            #   - если prev_side < 0, человек двигается наружу
            # Для углов 180-359 градусов - наоборот
            if 0 <= angle < 180:
                return True, "in" if prev_side > 0 else "out"
            else:
                return True, "in" if prev_side < 0 else "out"

        # Если линия не была пересечена
        return False, None

    def update_frame(self):
        """Детектирует, сопоставляет с предыдущими позициями и обновляет счетчик/кадр."""
        if not self.setup_mode:
            ret, frame, display_frame = self.get_optimized_frame()
            if ret:
                line_start, line_end = self.get_line_points(
                    frame.shape[1], frame.shape[0]
                )

                # Рисуем синюю линию подсчета
                cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

                # Обнаруживаем людей на текущем кадре
                people = self.detect_people(frame)

                # Словарь для хранения текущих позиций людей
                current_tracks = {}

                # Сопоставляем текущие детекции с предыдущими позициями
                used_prev_positions = set()
                used_current_detections = set()

                # Для каждой текущей детекции ищем ближайшую предыдущую позицию
                for i, box in enumerate(people):
                    x1, y1, x2, y2 = box
                    foot_position = (int((x1 + x2) / 2), y2)

                    # Ищем ближайшую предыдущую позицию
                    min_dist = float('inf')
                    best_prev_id = None

                    for prev_id, prev_pos in self.previous_positions.items():
                        if prev_id in used_prev_positions:
                            continue

                        # Вычисляем расстояние между текущей и предыдущей позицией
                        dist = math.sqrt(
                            (foot_position[0] - prev_pos[0])**2 +
                            (foot_position[1] - prev_pos[1])**2
                        )

                        # Если расстояние меньше порога и меньше предыдущего минимума
                        if dist < 100 and dist < min_dist:  # 100 пикселей - максимальное допустимое перемещение
                            min_dist = dist
                            best_prev_id = prev_id

                    # Если нашли соответствие
                    if best_prev_id is not None:
                        used_prev_positions.add(best_prev_id)
                        used_current_detections.add(i)
                        
                        # Проверяем пересечение линии
                        crossed, direction = self.check_line_crossing(
                            foot_position,
                            self.previous_positions[best_prev_id],
                            line_start,
                            line_end,
                        )

                        if crossed:
                            if direction == "in":
                                self.people_inside += 1
                            else:
                                self.people_inside = max(0, self.people_inside - 1)

                        # Обновляем позицию для этого ID
                        current_tracks[best_prev_id] = foot_position
                    else:
                        # Новая детекция - присваиваем новый ID
                        new_id = max(self.previous_positions.keys(), default=-1) + 1
                        current_tracks[new_id] = foot_position

                    # Рисуем рамку и точку
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(display_frame, foot_position, 5, (0, 0, 255), -1)

                # Обновляем счетчик на экране
                self.count_label.config(
                    text=f"Людей в помещении: {self.people_inside}"
                )

                # Обновляем словарь позиций
                self.previous_positions = current_tracks

                # Конвертируем кадр для отображения в Tkinter
                img = Image.fromarray(display_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

            # Планируем следующее обновление
            self.root.after(30, self.update_frame)

    def start_counting(self):
        """Переключает программу из режима настройки в режим подсчета людей

        Этот метод:
        1. Выключает режим настройки
        2. Убирает кнопку старта
        3. Показывает счетчик людей
        4. Запускает основной цикл обработки кадров
        """
        # Выключаем режим настройки линии
        self.setup_mode = False
        # Убираем кнопку "Начать подсчет"
        self.start_button.pack_forget()
        # Показываем рамку со счетчиком людей
        self.counter_frame.pack(pady=10)
        # Запускаем основной цикл обработки кадров
        self.update_frame()

    def __del__(self):
        """Деструктор класса - освобождает ресурсы при уничтожении объекта

        Этот метод автоматически вызывается Python при удалении объекта
        и гарантирует корректное освобождение ресурсов камеры
        """
        # Проверяем, была ли инициализирована камера
        if hasattr(self, "cap"):
            # Освобождаем ресурсы камеры
            self.cap.release()

    def process_video(self, input_path, output_path):
        """Обрабатывает видео из файла (пока не реализовано полностью)"""
        # Открываем видеофайл для чтения
        cap = cv2.VideoCapture(input_path)

        # Устанавливаем разрешение выходного видео 480p
        target_width = 854  # Стандартная ширина для 480p
        target_height = 480  # Стандартная высота для 480p

        # Создаем объект для записи видео
        fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Кодек для сжатия
        out = cv2.VideoWriter(
            output_path,  # Путь для сохранения
            fourcc,  # Используемый кодек
            30.0,  # Частота кадров (FPS)
            (target_width, target_height),  # Размер кадра
        )

        # Читаем и обрабатываем кадры из видео
        while cap.isOpened():
            # Читаем очередной кадр
            ret, frame = cap.read()
            if not ret:  # Если кадр не получен - выходим
                break

            # Изменяем размер кадра до 480p
            frame = cv2.resize(frame, (target_width, target_height))

            # Записываем обработанный кадр
            out.write(frame)


def main():
    root = tk.Tk()
    app = PeopleCounter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
