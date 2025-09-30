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
import tkinter as tk


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from people_counter import PeopleCounter

frame_queue = queue.Queue(maxsize=10)
command_queue = queue.Queue()
people_count = 0
counter_instance = None
root = None
setup_mode = True
stop_lock = threading.Lock()
stopping_in_progress = False


def create_tk_root():
    """Создает или возвращает скрытый Tk `root` для совместимости с Tk-интерфейсом."""
    global root
    if root is None:
        root = tk.Tk()
        root.withdraw()
    return root


class CounterThread(threading.Thread):
    """Фоновый поток камерного цикла, детекции и отрисовки кадра."""

    def __init__(self):
        super().__init__()
        self.running = True
        self.stopped = False
        self.daemon = True

    def run(self):
        """Основной цикл: сначала режим настройки, затем режим подсчета."""
        global root, counter_instance, setup_mode
        try:

            class ModifiedPeopleCounter(PeopleCounter):
                """Обертка над `PeopleCounter` c фиксацией рабочей директории и без preview."""

                def __init__(self, root):
                    current_dir = os.getcwd()
                    os.chdir(BASE_DIR)
                    super().__init__(root)
                    os.chdir(current_dir)

                def setup_preview(self):
                    """Отключает внутренний preview (используется собственная выдача кадров)."""
                    pass

            # Создаем экземпляр счетчика
            counter_instance = ModifiedPeopleCounter(create_tk_root())
            # Сбрасываем внутренние состояния счетчика к дефолту
            try:
                counter_instance.people_inside = 0
                counter_instance.previous_positions = {}
                if hasattr(counter_instance, "line_position") and hasattr(
                    counter_instance.line_position, "set"
                ):
                    counter_instance.line_position.set(50)
                if hasattr(counter_instance, "line_angle") and hasattr(
                    counter_instance.line_angle, "set"
                ):
                    counter_instance.line_angle.set(0)
            except Exception:
                pass

            # Запускаем в режиме настройки
            while self.running and setup_mode:
                try:
                    # Проверяем команды и обрабатываем кадры
                    self._process_commands()
                    self._process_frame(True)
                except Exception as e:
                    print(f"Ошибка в режиме настройки: {str(e)}")
                    break

            # Режим подсчета
            while self.running and not setup_mode:
                try:
                    self._process_commands()
                    self._process_frame(False)
                except Exception as e:
                    print(f"Ошибка в режиме подсчета: {str(e)}")
                    break

        except Exception as e:
            print(f"Критическая ошибка в потоке: {str(e)}")
        finally:
            self.cleanup()

    def _process_commands(self):
        """Считывает и применяет команды управления линией из очереди."""
        try:
            while True:
                cmd, value = command_queue.get_nowait()
                if cmd == "position":
                    counter_instance.line_position.set(value)
                elif cmd == "angle":
                    counter_instance.line_angle.set(value)
                command_queue.task_done()
        except queue.Empty:
            pass

    def _process_frame(self, is_setup_mode):
        """Готовит отображаемый кадр и, при необходимости, выполняет детекцию людей."""
        global people_count

        if not counter_instance:
            return

        ret, frame, display_frame = counter_instance.get_optimized_frame()
        if not ret:
            return

        line_start, line_end = counter_instance.get_line_points(
            display_frame.shape[1], display_frame.shape[0]
        )

        if is_setup_mode:
            cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)
        else:
            # Обработка режима подсчета
            people = counter_instance.detect_people(frame)
            cv2.line(display_frame, line_start, line_end, (255, 0, 0), 2)

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
            people_count = counter_instance.people_inside

        # Отправляем кадр в очередь
        _, buffer = cv2.imencode(".jpg", display_frame)
        try:
            frame_queue.put_nowait(buffer.tobytes())
        except queue.Full:
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
            frame_queue.put(buffer.tobytes())

    def cleanup(self):
        """Освобождает ресурсы (очереди, OpenCV, Tk) и сбрасывает состояние."""
        global counter_instance, root

        print("Начинаем очистку ресурсов...")

        # Очищаем очереди
        self._clear_queue(frame_queue)
        self._clear_queue(command_queue)

        # Освобождаем ресурсы OpenCV
        if counter_instance:
            try:
                counter_instance.cap.release()
            except Exception:
                pass
            counter_instance = None

        # Закрываем окно Tkinter
        if root:
            try:
                root.quit()
                root.destroy()
            except Exception:
                pass
            root = None

        print("Очистка ресурсов завершена")

    def stop(self):
        """Останавливает поток и запускает очистку."""
        if not self.stopped:
            print("Останавливаем поток...")
            self.running = False
            self.stopped = True
            self.cleanup()

    def _clear_queue(self, q):
        """Полностью освобождает указанную очередь без блокировок."""
        try:
            while True:
                q.get_nowait()
                q.task_done()
        except queue.Empty:
            pass


counter_thread = None


class StartCounterView(APIView):
    """Стартует поток и включает режим настройки."""

    def post(self, request):
        global counter_thread, setup_mode, people_count, counter_instance
        if counter_thread is None or not counter_thread.is_alive():
            setup_mode = True
            people_count = 0
            counter_thread = CounterThread()
            counter_thread.start()
        return Response({"status": "started"})


class StopCounterView(APIView):
    """Останавливает поток и безопасно освобождает ресурсы."""

    def post(self, request):
        global counter_thread, counter_instance, root, stopping_in_progress
        with stop_lock:
            if stopping_in_progress:
                return Response({"status": "stop_in_progress"}, status=429)

            if not counter_thread or not counter_thread.is_alive():
                return Response({"status": "already_stopped"}, status=400)

            try:
                stopping_in_progress = True
                print("Получен запрос на остановку...")

                if not counter_thread.stopped:
                    print("Останавливаем поток...")
                    counter_thread.stop()
                    print("Ожидаем завершения потока...")
                    counter_thread.join(timeout=3.0)

                    if counter_thread.is_alive():
                        print(
                            "Поток не завершился корректно, принудительно завершаем..."
                        )
                        if counter_instance:
                            try:
                                counter_instance.cap.release()
                            except Exception:
                                pass
                            counter_instance = None

                        if root:
                            try:
                                root.quit()
                                root.destroy()
                            except Exception:
                                pass
                            root = None

                counter_thread = None
                print("Остановка завершена")
                stopping_in_progress = False
                return Response({"status": "stopped"})

            except Exception as e:
                print(f"Ошибка при остановке: {str(e)}")
                # Принудительная очистка всех ресурсов в случае ошибки
                try:
                    if counter_instance:
                        counter_instance.cap.release()
                    if root:
                        root.quit()
                        root.destroy()
                except Exception:
                    pass

                counter_thread = None
                counter_instance = None
                root = None
                stopping_in_progress = False

                return Response(
                    {"status": "error", "message": f"Ошибка при остановке: {str(e)}"},
                    status=500,
                )


class UpdateLineSettingsView(APIView):
    """Обновляет положение и угол линии через очередь команд."""

    def post(self, request):
        global counter_instance
        if counter_instance:
            position = request.data.get("position", 50)
            angle = request.data.get("angle", 0)
            command_queue.put(("position", position))
            command_queue.put(("angle", angle))
        return Response({"status": "updated"})


class StartCountingView(APIView):
    """Переключает систему из режима настройки в режим подсчета."""

    def post(self, request):
        global setup_mode
        setup_mode = False
        return Response({"status": "counting_started"})


def video_feed(request):
    """Возвращает MJPEG-поток кадров для фронтенда."""

    def generate():
        global counter_thread
        while True:
            if (
                not counter_thread
                or not counter_thread.is_alive()
                or counter_thread.stopped
            ):
                print("Видеопоток остановлен")
                break

            try:
                frame_bytes = frame_queue.get(timeout=0.5)
                if frame_bytes:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                    )
            except queue.Empty:
                if not counter_thread or counter_thread.stopped:
                    print("Поток остановлен, прерываем видеопоток")
                    break
                continue
            except Exception as e:
                print(f"Ошибка в видеопотоке: {str(e)}")
                break

    response = StreamingHttpResponse(
        generate(), content_type="multipart/x-mixed-replace; boundary=frame", status=200
    )
    # Запрещаем кэширование, чтобы браузер не показывал старые кадры
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


class GetCountView(APIView):
    """Возвращает текущее значение счетчика людей."""

    def get(self, request):
        return Response({"count": people_count})
