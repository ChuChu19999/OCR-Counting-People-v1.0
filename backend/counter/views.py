from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import cv2
import base64
import numpy as np
import threading
import queue
import sys
import os

# Абсолютный путь к корневой директории проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Добавляем путь к корневой директории проекта
sys.path.append(BASE_DIR)

# Импортируем PeopleCounter из корневой директории
from people_counter import PeopleCounter
import tkinter as tk

# Глобальные переменные для хранения состояния
frame_queue = queue.Queue(maxsize=10)
command_queue = queue.Queue()  # Очередь для команд (решение проблемы с ошибкой асинка)
people_count = 0
counter_instance = None
root = None
setup_mode = True


class CounterThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        global root, counter_instance, setup_mode
        root = tk.Tk()
        root.withdraw()  # Скрываем основное окно Tkinter

        # Модифицируем класс PeopleCounter для использования абсолютных путей
        class ModifiedPeopleCounter(PeopleCounter):
            def __init__(self, root):
                # Сохраняем текущую директорию
                current_dir = os.getcwd()
                # Переходим в корневую директорию проекта
                os.chdir(BASE_DIR)
                # Инициализируем родительский класс
                super().__init__(root)
                # Возвращаемся в исходную директорию
                os.chdir(current_dir)

        counter_instance = ModifiedPeopleCounter(root)

        # Запускаем в режиме настройки
        while self.running and setup_mode:
            # Проверяем наличие команд
            try:
                while True:  # Обрабатываем все команды в очереди
                    cmd, value = command_queue.get_nowait()
                    if cmd == "position":
                        counter_instance.line_position.set(value)
                    elif cmd == "angle":
                        counter_instance.line_angle.set(value)
                    command_queue.task_done()
            except queue.Empty:
                pass

            ret, _, display_frame = counter_instance.get_optimized_frame()
            if ret:
                # Получаем точки линии
                line_start, line_end = counter_instance.get_line_points(
                    display_frame.shape[1], display_frame.shape[0]
                )
                # Рисуем линию
                cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)
                # Добавляем текст-подсказку
                cv2.putText(
                    display_frame,
                    "Настройте положение и угол линии",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )
                # Конвертируем кадр в JPEG
                _, buffer = cv2.imencode(".jpg", display_frame)
                try:
                    frame_queue.put_nowait(buffer.tobytes())
                except queue.Full:
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    frame_queue.put(buffer.tobytes())

            # Обновляем Tkinter
            root.update()

        # После выхода из режима настройки запускаем подсчет
        while self.running and not setup_mode:
            # Проверяем наличие команд
            try:
                while True:  # Обрабатываем все команды в очереди
                    cmd, value = command_queue.get_nowait()
                    if cmd == "position":
                        counter_instance.line_position.set(value)
                    elif cmd == "angle":
                        counter_instance.line_angle.set(value)
                    command_queue.task_done()
            except queue.Empty:
                pass

            ret, frame, display_frame = counter_instance.get_optimized_frame()
            if ret:
                # Получаем точки линии
                line_start, line_end = counter_instance.get_line_points(
                    display_frame.shape[1], display_frame.shape[0]
                )

                # Обнаруживаем людей
                people = counter_instance.detect_people(frame)

                # Рисуем линию
                cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

                # Обрабатываем каждого обнаруженного человека
                current_tracks = {}
                for i, box in enumerate(people):
                    x1, y1, x2, y2 = box
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    foot_position = (int((x1 + x2) / 2), y2)
                    cv2.circle(display_frame, foot_position, 5, (0, 0, 255), -1)

                    if i in counter_instance.previous_positions:
                        crossed, direction = counter_instance.check_line_crossing(
                            foot_position,
                            counter_instance.previous_positions[i],
                            line_start,
                            line_end,
                        )
                        if crossed:
                            if direction == "in":
                                counter_instance.people_inside += 1
                            else:
                                counter_instance.people_inside = max(
                                    0, counter_instance.people_inside - 1
                                )

                    current_tracks[i] = foot_position

                counter_instance.previous_positions = current_tracks

                # Конвертируем кадр в JPEG
                _, buffer = cv2.imencode(".jpg", display_frame)
                try:
                    frame_queue.put_nowait(buffer.tobytes())
                except queue.Full:
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                    frame_queue.put(buffer.tobytes())

            # Обновляем счетчик людей
            global people_count
            people_count = counter_instance.people_inside

            # Обновляем Tkinter
            root.update()

    def stop(self):
        self.running = False
        if root:
            root.quit()


counter_thread = None


class StartCounterView(APIView):
    def post(self, request):
        global counter_thread, setup_mode
        if counter_thread is None or not counter_thread.is_alive():
            setup_mode = True  # Начинаем с режима настройки
            counter_thread = CounterThread()
            counter_thread.start()
        return Response({"status": "started"})


class StopCounterView(APIView):
    def post(self, request):
        global counter_thread
        if counter_thread and counter_thread.is_alive():
            counter_thread.stop()
            counter_thread.join()
            counter_thread = None
        return Response({"status": "stopped"})


class UpdateLineSettingsView(APIView):
    def post(self, request):
        global counter_instance
        if counter_instance:
            position = request.data.get("position", 50)
            angle = request.data.get("angle", 0)
            # Добавляем команды в очередь вместо прямого вызова
            command_queue.put(("position", position))
            command_queue.put(("angle", angle))
        return Response({"status": "updated"})


class StartCountingView(APIView):
    def post(self, request):
        global setup_mode
        setup_mode = False
        return Response({"status": "counting_started"})


def video_feed(request):
    def generate():
        while True:
            try:
                frame_bytes = frame_queue.get(timeout=1.0)
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
            except queue.Empty:
                continue

    return StreamingHttpResponse(
        generate(), content_type="multipart/x-mixed-replace; boundary=frame"
    )


class GetCountView(APIView):
    def get(self, request):
        return Response({"count": people_count})
