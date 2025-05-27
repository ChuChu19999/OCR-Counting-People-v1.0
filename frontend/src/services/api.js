import axios from "axios";
import { API_BASE_URL, ENDPOINTS } from "../constants";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const updateLineSettings = async (position, angle) => {
  try {
    const response = await api.post(ENDPOINTS.UPDATE_LINE, {
      position,
      angle,
    });
    return response.data;
  } catch (error) {
    console.error("Ошибка при обновлении настроек линии:", error);
    throw error;
  }
};

export const getPeopleCount = async () => {
  try {
    const response = await api.get(ENDPOINTS.COUNT);
    return response.data.count;
  } catch (error) {
    console.error("Ошибка при получении количества людей:", error);
    throw error;
  }
};

export const startSystem = async () => {
  try {
    const response = await api.post(ENDPOINTS.START);
    return response.data;
  } catch (error) {
    console.error("Ошибка при запуске системы:", error);
    throw error;
  }
};

export const startCounting = async () => {
  try {
    const response = await api.post(ENDPOINTS.START_COUNTING);
    return response.data;
  } catch (error) {
    console.error("Ошибка при запуске подсчета:", error);
    throw error;
  }
};

export const stopSystem = async () => {
  try {
    const response = await api.post(ENDPOINTS.STOP);
    return response;
  } catch (error) {
    console.error("Ошибка при остановке системы:", error);
    throw error;
  }
};
