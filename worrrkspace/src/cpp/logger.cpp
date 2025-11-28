#include "logger.h"
#include <iostream>
#include <chrono>
#include <sstream>
#include <iomanip>
#include <windows.h>  // Добавляем для работы с кодировкой

Logger::Logger(const std::string& filename) : filename(filename) {
    // Создаем папку logs
    system("mkdir logs 2>nul");

    // Устанавливаем кодировку консоли для Windows
    SetConsoleOutputCP(CP_UTF8);

    logfile.open("logs/" + filename, std::ios::app);
    if (!logfile.is_open()) {
        throw std::runtime_error("Cannot open log file: logs/" + filename);
    }
}

void Logger::log(const std::string& level, const std::string& message) {
    std::string timestamp = getCurrentTime();
    logfile << "[" << timestamp << "] [" << level << "] " << message << std::endl;

    // Вывод в консоль с правильной кодировкой
    std::cout << "[" << timestamp << "] [" << level << "] " << message << std::endl;
}

// ЗАМЕНИТЕ функцию getCurrentTime на:
std::string Logger::getCurrentTime() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);

    std::stringstream ss;
    ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
    return ss.str();
}

Logger::~Logger() {
    if (logfile.is_open()) {
        logfile.close();
    }
}

// C интерфейс
extern "C" {
    __declspec(dllexport) Logger* create_logger(const char* filename) {
        try {
            return new Logger(filename);
        }
        catch (...) {
            return nullptr;
        }
    }

    __declspec(dllexport) void logger_log(Logger* logger, const char* level, const char* message) {
        if (logger) {
            logger->log(level, message);
        }
    }

    __declspec(dllexport) void delete_logger(Logger* logger) {
        if (logger) {
            delete logger;
        }
    }
}