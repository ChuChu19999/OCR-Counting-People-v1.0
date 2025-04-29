// Конфигурация API
const API_BASE_URL = 'http://localhost:8000/api';

// DOM элементы
const videoFeed = document.getElementById('videoFeed');
const startButton = document.getElementById('startButton');
const startCountingButton = document.getElementById('startCountingButton');
const stopButton = document.getElementById('stopButton');
const peopleCount = document.getElementById('peopleCount');
const linePosition = document.getElementById('linePosition');
const lineAngle = document.getElementById('lineAngle');

// Состояние приложения
let isRunning = false;
let countUpdateInterval = null;
let isStoppingInProgress = false;  // Добавляем флаг для отслеживания процесса остановки

// Функция для обновления настроек линии
async function updateLineSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/update_line/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                position: linePosition.value,
                angle: lineAngle.value
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка при обновлении настроек линии');
        }
    } catch (error) {
        console.error('Ошибка при обновлении настроек:', error);
    }
}

// Функция для обновления счетчика людей
async function updatePeopleCount() {
    try {
        const response = await fetch(`${API_BASE_URL}/count/`);
        const data = await response.json();
        peopleCount.textContent = data.count;
    } catch (error) {
        console.error('Ошибка при получении количества людей:', error);
    }
}

// Функция для запуска системы подсчета
async function startCounter() {
    try {
        // Отправляем запрос на запуск
        const response = await fetch(`${API_BASE_URL}/start/`, {
            method: 'POST'
        });
        
        if (response.ok) {
            isRunning = true;
            startButton.disabled = true;
            startCountingButton.disabled = false;
            stopButton.disabled = false;

            // Устанавливаем источник видео
            videoFeed.src = `${API_BASE_URL}/video_feed/`;

            // Добавляем обработчики событий для слайдеров
            linePosition.addEventListener('input', updateLineSettings);
            lineAngle.addEventListener('input', updateLineSettings);
        }
    } catch (error) {
        console.error('Ошибка при запуске системы:', error);
    }
}

// Функция для начала подсчета
async function startCounting() {
    try {
        const response = await fetch(`${API_BASE_URL}/start_counting/`, {
            method: 'POST'
        });
        
        if (response.ok) {
            startCountingButton.disabled = true;
            linePosition.disabled = true;
            lineAngle.disabled = true;

            // Запускаем периодическое обновление счетчика
            countUpdateInterval = setInterval(updatePeopleCount, 1000);
        }
    } catch (error) {
        console.error('Ошибка при запуске подсчета:', error);
    }
}

// Функция для остановки системы подсчета
async function stopCounter() {
    // Проверяем, не выполняется ли уже остановка
    if (isStoppingInProgress) {
        console.log('Остановка уже в процессе...');
        return;
    }

    try {
        isStoppingInProgress = true;
        stopButton.disabled = true;  // Блокируем кнопку
        stopButton.textContent = 'Останавливается...';  // Меняем текст кнопки

        // Отправляем запрос на остановку
        const response = await fetch(`${API_BASE_URL}/stop/`, {
            method: 'POST'
        });
        
        if (response.status === 200) {
            console.log('Система успешно остановлена');
            isRunning = false;
            startButton.disabled = false;
            startCountingButton.disabled = true;
            linePosition.disabled = false;
            lineAngle.disabled = false;

            // Очищаем видео
            videoFeed.src = '';

            // Останавливаем обновление счетчика
            if (countUpdateInterval) {
                clearInterval(countUpdateInterval);
                countUpdateInterval = null;
            }

            // Удаляем обработчики событий слайдеров
            linePosition.removeEventListener('input', updateLineSettings);
            lineAngle.removeEventListener('input', updateLineSettings);
        } else if (response.status === 429) {
            console.log('Остановка уже выполняется...');
        } else if (response.status === 400) {
            console.log('Система уже остановлена');
            isRunning = false;
            startButton.disabled = false;
            startCountingButton.disabled = true;
            stopButton.disabled = true;
        } else {
            throw new Error(`Неожиданный статус ответа: ${response.status}`);
        }
    } catch (error) {
        console.error('Ошибка при остановке системы:', error);
    } finally {
        isStoppingInProgress = false;
        stopButton.disabled = !isRunning;  // Активируем кнопку только если система запущена
        stopButton.textContent = 'Остановить';  // Возвращаем исходный текст кнопки
    }
}

// Обработчики событий
startButton.addEventListener('click', startCounter);
startCountingButton.addEventListener('click', startCounting);
stopButton.addEventListener('click', stopCounter);

// Обработка ошибок видеопотока
videoFeed.addEventListener('error', () => {
    console.error('Ошибка при загрузке видеопотока');
    stopCounter();
}); 