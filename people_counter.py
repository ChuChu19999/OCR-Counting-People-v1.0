# Импортируем все необходимые библиотеки для работы программы
import cv2  # OpenCV - библиотека для работы с видео и изображениями
import numpy as np  # NumPy - библиотека для работы с массивами и матрицами
import tkinter as tk  # Tkinter - библиотека для создания графического интерфейса
from tkinter import (
    ttk,
)  # ttk - современные виджеты
from PIL import (
    Image,
    ImageTk,
)  # PIL - для работы с изображениями и конвертации их для Tkinter
import math  # Математические функции (sin, cos, sqrt и т.д.)
import ultralytics  # Основная библиотека YOLOv8
from ultralytics import (
    YOLO,
)  # Импортируем конкретно YOLO модель для распознавания объектов


# Класс для подсчета людей в помещении
class PeopleCounter:
    def __init__(self, root):
        # root - это главное окно приложения, которое мы получаем из Tkinter
        self.root = root
        # Устанавливаем заголовок окна программы
        self.root.title("Система подсчета людей")

        # Загружаем предобученную модель YOLOv8n для распознавания объектов
        # 'yolov8n.pt' - это самая маленькая и быстрая версия модели
        self.model = YOLO("yolov8n.pt")

        # Открываем файл с названиями классов, которые может распознать YOLO
        # coco.names содержит список всех объектов, которые умеет распознавать модель
        with open("coco.names", "r") as f:
            # Читаем все классы в список, убирая лишние пробелы
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

        # Создаем все элементы интерфейса (кнопки, слайдеры и т.д.)
        self.setup_ui()

        # Инициализируем камеру (0 - обычно встроенная камера ноутбука)
        self.cap = cv2.VideoCapture(0)
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
        """Вычисляет координаты начала и конца линии подсчета на основе настроек слайдеров"""
        # Вычисляем Y-координату линии, преобразуя значение слайдера (0-100)
        # в реальные координаты кадра
        line_y = int(frame_height * self.line_position.get() / 100)
        # Получаем текущий угол поворота линии из слайдера
        angle = self.line_angle.get()

        # Находим центральную точку линии
        center_x = frame_width // 2  # Центр по горизонтали - половина ширины кадра
        center_y = line_y  # Позиция по вертикали из слайдера

        # Вычисляем длину линии, используя теорему Пифагора
        # Берем длину больше диагонали кадра, чтобы линия всегда пересекала весь кадр
        line_length = math.sqrt(frame_width**2 + frame_height**2)
        half_length = line_length / 2  # Половина длины для расчета от центра

        # Переводим угол из градусов в радианы для тригонометрических функций
        angle_rad = math.radians(angle)

        # Вычисляем координаты первой точки линии (x1, y1)
        # Используем косинус для X координаты и синус для Y координаты
        x1 = center_x + half_length * math.cos(angle_rad)
        y1 = center_y + half_length * math.sin(angle_rad)

        # Вычисляем координаты второй точки линии (x2, y2)
        # Для второй точки идем в противоположном направлении от центра
        x2 = center_x - half_length * math.cos(angle_rad)
        y2 = center_y - half_length * math.sin(angle_rad)

        # Возвращаем кортеж с целочисленными координатами обеих точек
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
        """Получает и подготавливает кадр с камеры для дальнейшей обработки

        Returns:
            tuple: (успех, исходный кадр, кадр для отображения)
            - успех (bool): True если кадр получен успешно
            - исходный кадр: numpy array с BGR изображением для обработки
            - кадр для отображения: копия кадра для рисования на нем
        """
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
        """Обнаруживает людей на кадре с помощью YOLO

        Args:
            frame: numpy array с BGR изображением

        Returns:
            list: Список координат обнаруженных людей в формате [x1, y1, x2, y2]
                 где (x1,y1) - верхний левый угол, (x2,y2) - нижний правый угол
        """
        # Запускаем YOLO для обнаружения только класса 'person' (индекс 0)
        # classes=0 говорит модели искать только людей
        results = self.model(frame, classes=0)

        # Список для хранения координат обнаруженных людей
        boxes = []

        # Обрабатываем результаты детекции
        for result in results:
            # Перебираем все найденные объекты
            for box in result.boxes:
                # Проверяем уверенность модели (confidence)
                # Если модель уверена больше чем на 50%, добавляем объект
                if box.conf > 0.5:
                    # Получаем координаты рамки из результатов YOLO
                    # xyxy возвращает координаты в формате [x1, y1, x2, y2]
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                    # Преобразуем координаты в целые числа и добавляем в список
                    boxes.append([int(x1), int(y1), int(x2), int(y2)])

        return boxes

    def setup_preview(self):
        """Предварительный просмотр для настройки линии"""
        ret, _, display_frame = self.get_optimized_frame()
        if ret:
            # Получаем точки линии
            line_start, line_end = self.get_line_points(
                display_frame.shape[1], display_frame.shape[0]
            )

            # Рисуем линию
            cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

            # Добавляем текст-подсказку
            cv2.putText(
                display_frame,
                "Установите положение и угол линии, затем нажмите 'Начать подсчет'",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Конвертируем кадр для отображения в tkinter
            img = Image.fromarray(display_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        if self.setup_mode:
            self.root.after(30, self.setup_preview)

    def check_line_crossing(self, current_pos, previous_pos, line_start, line_end):
        """Проверяет, пересек ли человек линию подсчета

        Args:
            current_pos: текущие координаты человека (x, y)
            previous_pos: предыдущие координаты человека (x, y)
            line_start: начальная точка линии (x, y)
            line_end: конечная точка линии (x, y)

        Returns:
            tuple: (произошло_пересечение, направление)
            - произошло_пересечение (bool): True если линия была пересечена
            - направление (str): "in" если человек вошел, "out" если вышел
        """
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
        """Основной метод обработки кадров и подсчета пересечений

        Этот метод выполняется циклически и:
        1. Получает новый кадр с камеры
        2. Обнаруживает людей на кадре
        3. Отслеживает их перемещения
        4. Проверяет пересечение линии
        5. Обновляет счетчик
        6. Отображает результаты
        """
        # Проверяем, что мы не в режиме настройки
        if not self.setup_mode:
            # Получаем новый кадр с камеры
            ret, frame, display_frame = self.get_optimized_frame()
            if ret:  # Если кадр успешно получен
                # Вычисляем текущие координаты линии подсчета
                line_start, line_end = self.get_line_points(
                    frame.shape[1], frame.shape[0]
                )

                # Рисуем синюю линию подсчета
                cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

                # Обнаруживаем людей на текущем кадре
                people = self.detect_people(frame)

                # Словарь для хранения текущих позиций людей
                # Ключ - ID человека, значение - его координаты
                current_tracks = {}

                # Обрабатываем каждого обнаруженного человека
                for i, box in enumerate(people):
                    # Получаем координаты рамки
                    x1, y1, x2, y2 = box

                    # Рисуем зеленую рамку вокруг человека
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Вычисляем позицию ног (центр нижней части рамки)
                    # Используем нижнюю точку, так как она более стабильна для отслеживания
                    foot_position = (int((x1 + x2) / 2), y2)

                    # Рисуем красную точку в позиции ног для отладки
                    cv2.circle(display_frame, foot_position, 5, (0, 0, 255), -1)

                    # Если у этого человека есть предыдущая позиция
                    if i in self.previous_positions:
                        # Проверяем, пересек ли человек линию
                        crossed, direction = self.check_line_crossing(
                            foot_position,
                            self.previous_positions[i],
                            line_start,
                            line_end,
                        )

                        # Если произошло пересечение линии
                        if crossed:
                            if direction == "in":
                                # Увеличиваем счетчик людей внутри
                                self.people_inside += 1
                            else:
                                # Уменьшаем счетчик, но не меньше 0
                                self.people_inside = max(0, self.people_inside - 1)

                            # Обновляем текст счетчика на экране
                            self.count_label.config(
                                text=f"Людей в помещении: {self.people_inside}"
                            )

                    # Сохраняем текущую позицию для следующего кадра
                    current_tracks[i] = foot_position

                # Обновляем словарь позиций
                self.previous_positions = current_tracks

                # Конвертируем кадр из BGR в формат для отображения в Tkinter
                img = Image.fromarray(display_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

            # Планируем следующее обновление через 30 миллисекунд
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
        """Обрабатывает видео из файла (пока не реализовано полностью)

        Args:
            input_path: путь к входному видеофайлу
            output_path: путь для сохранения обработанного видео
        """
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
    """Точка входа в программу

    Создает главное окно приложения и запускает его
    """
    # Создаем главное окно Tkinter
    root = tk.Tk()
    # Создаем экземпляр нашего приложения
    app = PeopleCounter(root)
    # Запускаем главный цикл обработки событий
    root.mainloop()


# Проверяем, что скрипт запущен напрямую (не импортирован)
if __name__ == "__main__":
    # Запускаем приложение
    main()
