#pragma once
#include <string>
#include <fstream>
#include <ctime>

class Logger {
public:
    Logger(const std::string& filename);
    void log(const std::string& level, const std::string& message);
    ~Logger();

private:
    std::string getCurrentTime();
    std::ofstream logfile;
    std::string filename;
};

// C интерфейс
extern "C" {
    __declspec(dllexport) Logger* create_logger(const char* filename);
    __declspec(dllexport) void logger_log(Logger* logger, const char* level, const char* message);
    __declspec(dllexport) void delete_logger(Logger* logger);
}