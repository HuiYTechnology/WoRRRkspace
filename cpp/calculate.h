#pragma once
#ifndef CALCULATE_H
#define CALCULATE_H

#include "msvc_config.h"

#include "logger.h"
#include <vector>
#include <string>
#include <cmath>
#include <stdexcept>
#include <unordered_map>
#include <memory>

class BigNumber {
private:
    std::vector<int> digits;  // цифры (0-9), digits[0] - младший разряд (LSB first)
    int decimalPoint;        // позиция десятичной точки (количество цифр после запятой)
    static const std::string LN_10;  // ln(10) с высокой точностью

public:
    bool negative;           // знак числа

    BigNumber();
    BigNumber(const std::string& str);
    BigNumber(double value);
    BigNumber(const std::vector<int>& digits, bool negative, int decimalPoint);

    // Конструкторы копирования и перемещения для совместимости с MSVC
    BigNumber(const BigNumber&) = default;
    BigNumber(BigNumber&&) = default;
    BigNumber& operator=(const BigNumber&) = default;
    BigNumber& operator=(BigNumber&&) = default;

    std::string toString() const;
    int getPrecision() const;
    void setPrecision(int precision);

    // Арифметические операции с произвольной точностью
    BigNumber add(const BigNumber& other) const;
    BigNumber subtract(const BigNumber& other) const;
    BigNumber multiply(const BigNumber& other) const;
    BigNumber divide(const BigNumber& other, int precision = 50) const;

    // Перегруженные операторы
    BigNumber operator+(const BigNumber& other) const { return add(other); }
    BigNumber operator-(const BigNumber& other) const { return subtract(other); }
    BigNumber operator*(const BigNumber& other) const { return multiply(other); }
    BigNumber operator/(const BigNumber& other) const { return divide(other); }
    BigNumber operator-() const;

    // Математические функции
    BigNumber power(const BigNumber& exponent, int precision = 50) const;
    BigNumber factorial() const;
    BigNumber sin(int precision = 60) const;
    BigNumber cos(int precision = 60) const;
    BigNumber tan(int precision = 60) const;
    BigNumber ln(int precision = 50) const;
    BigNumber log10(int precision = 50) const;
    BigNumber exp(int precision = 50) const;

    // Вспомогательные методы
    static BigNumber pi(int precision = 100);
    static BigNumber e(int precision = 100);
    bool isZero() const;
    BigNumber abs() const;
    BigNumber negate() const;

    // Вспомогательные методы для алгоритма Кнута (оставлены для совместимости)
    void normalize();
    void denormalize(int divisor);
    int estimateQuotient(const BigNumber& divisor) const;
    void multiplyByDigit(int digit);
    void divideByDigit(int digit);
    bool isNormalized() const;

    // Алгоритм деления
    BigNumber divideKnuth(const BigNumber& other, int precision) const;

    // ОТЛАДОЧНЫЕ МЕТОДЫ
    int getDecimalPoint() const { return decimalPoint; }
    std::vector<int> getDigits() const { return digits; }
    bool isNegative() const { return negative; }
    std::string debugString() const;

    int compare(const BigNumber& other) const;
    static BigNumber compute_ln2(int precision);
    static BigNumber compute_ln10(int precision);
    BigNumber ln_direct(int precision) const;
    BigNumber mod2Pi(int precision) const;

private:
    void reduceToFirstQuadrant(const BigNumber& x, BigNumber& reducedX, int& quadrant, int precision);
    BigNumber sin_taylor_small(const BigNumber& x, int precision) const;
    BigNumber cos_taylor_small(const BigNumber& x, int precision) const;
    BigNumber sin_high_precision(int precision) const;
    BigNumber cos_high_precision(int precision) const;
    BigNumber divideSimple(const BigNumber& other, int precision) const;
    void removeLeadingZeros();
    void alignDecimals(BigNumber& other, int& newDecimal);
    std::vector<int> addArrays(const std::vector<int>& a, const std::vector<int>& b) const;
    std::vector<int> subtractArrays(const std::vector<int>& a, const std::vector<int>& b) const;
    std::vector<int> multiplyArrays(const std::vector<int>& a, const std::vector<int>& b) const;

    int compareArrays(const std::vector<int>& a, const std::vector<int>& b) const;

    // helper: long division on decimal strings (MSB-first)
    static std::string longDivStrings(const std::string& dividend, const std::string& divisor);

    // utility trim for LSB-first vectors
    static void trimLSBVector(std::vector<int>& a);
};

class Calculator {
private:
    class Logger* logger;
    int precision;

    // Кэш для хранения результатов вычислений
    struct CacheKey {
        std::string expression;
        int precision;

        bool operator==(const CacheKey& other) const {
            return expression == other.expression && precision == other.precision;
        }
    };

    struct CacheKeyHash {
        std::size_t operator()(const CacheKey& key) const {
            return std::hash<std::string>{}(key.expression) ^
                (std::hash<int>{}(key.precision) << 1);
        }
    };

    std::unordered_map<CacheKey, BigNumber, CacheKeyHash> cache;

public:
    Calculator(Logger* logger = nullptr, int precision = 50);
    void setPrecision(int newPrecision);
    int getPrecision() const { return precision; }

    BigNumber evaluate(const std::string& expression);
    void clearCache() { cache.clear(); } // Новый метод для очистки кэша

private:
    std::vector<std::string> tokenize(const std::string& expression);
    BigNumber parseExpression(const std::vector<std::string>& tokens, size_t& index);
    BigNumber parseTerm(const std::vector<std::string>& tokens, size_t& index);
    BigNumber parseFactor(const std::vector<std::string>& tokens, size_t& index);
    BigNumber parseNumber(const std::vector<std::string>& tokens, size_t& index);
    BigNumber parseFunction(const std::string& funcName, const std::vector<std::string>& tokens, size_t& index);

    // Вспомогательные методы для кэширования
    BigNumber evaluateWithCache(const std::string& expression, const std::vector<std::string>& tokens, size_t start, size_t end);
    std::string getSubExpression(const std::vector<std::string>& tokens, size_t start, size_t end);

    void log(const std::string& level, const std::string& message);
};

// C interface
extern "C" {
    __declspec(dllexport) Calculator* create_calculator_with_precision(int precision);
    __declspec(dllexport) Calculator* create_calculator();
    __declspec(dllexport) char* calculate_expression(Calculator* calc, const char* expression);
    __declspec(dllexport) void delete_calculator(Calculator* calc);
    __declspec(dllexport) void free_result(char* result);
    __declspec(dllexport) void set_calculator_precision(Calculator* calc, int precision);
    __declspec(dllexport) int get_calculator_precision(Calculator* calc);
}

#endif