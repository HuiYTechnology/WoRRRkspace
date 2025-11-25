#pragma once
#include "calculate.h"
#include <sstream>
#include <stack>
#include <algorithm>
#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <cstring>
#include <stdexcept>
#include <cctype>

// ------------------ Конструкторы и базовые методы ------------------

BigNumber::BigNumber() : digits({ 0 }), negative(false), decimalPoint(0) {}

BigNumber::BigNumber(const std::string& str) : negative(false), decimalPoint(0) {
    std::string s = str;
    // trim spaces
    s.erase(std::remove_if(s.begin(), s.end(), ::isspace), s.end());
    if (s.empty()) {
        digits = { 0 };
        negative = false;
        decimalPoint = 0;
        return;
    }

    if (s[0] == '+') s = s.substr(1);
    if (!s.empty() && s[0] == '-') {
        negative = true;
        s = s.substr(1);
    }

    size_t dot = s.find('.');
    if (dot != std::string::npos) {
        decimalPoint = (int)(s.size() - dot - 1);
        s.erase(dot, 1);
    }

    // remove leading zeros in MSB side of the string
    size_t pos = 0;
    while (pos + 1 < s.size() && s[pos] == '0') ++pos;
    if (pos > 0) s = s.substr(pos);

    // digits vector is LSB-first: digits[0] is least significant
    digits.clear();
    for (int i = (int)s.size() - 1; i >= 0; --i) {
        if (!isdigit((unsigned char)s[i])) throw std::invalid_argument("Invalid character in number");
        digits.push_back(s[i] - '0');
    }
    if (digits.empty()) digits.push_back(0);
    removeLeadingZeros();
}

BigNumber::BigNumber(double value) {
    std::stringstream ss;
    ss.precision(15);
    ss << value;
    *this = BigNumber(ss.str());
}

BigNumber::BigNumber(const std::vector<int>& digits_, bool negative_, int decimalPoint_)
    : digits(digits_), negative(negative_), decimalPoint(decimalPoint_) {
    removeLeadingZeros();
}

std::string BigNumber::toString() const {
    if (isZero()) return "0";

    std::string s;
    if (negative) s.push_back('-');

    // Build MSB-first string from digits (digits LSB-first)
    int n = (int)digits.size();
    for (int i = n - 1; i >= 0; --i) s.push_back(char('0' + digits[i]));

    // Insert decimal point if needed
    if (decimalPoint > 0) {
        int pos = (int)s.size() - decimalPoint;
        if (s[0] == '-') pos -= 1; // adjust for sign
        // If pos <= sign position, we need to add leading "0."
        if (pos <= (negative ? 1 : 0)) {
            // build: sign + "0." + leading zeros + digits
            std::string digitsOnly = (negative ? s.substr(1) : s);
            std::string res;
            if (negative) res.push_back('-');
            res += "0.";
            int zeros = (decimalPoint - (int)digitsOnly.size());
            if (zeros < 0) zeros = 0;
            for (int i = 0; i < zeros; ++i) res.push_back('0');
            res += digitsOnly;
            return res;
        }
        else {
            // insert '.' before character at position pos
            if (negative) pos = pos - 1; // because s includes sign
            s.insert(s.size() - decimalPoint, ".");
        }
    }
    return s;
}

int BigNumber::getPrecision() const {
    return (int)digits.size();
}

void BigNumber::setPrecision(int precision) {
    if (precision < 0) return;

    if (decimalPoint > precision) {
        // Уменьшаем количество цифр после десятичной точки до precision
        int digitsToRemove = decimalPoint - precision;

        // Проверяем необходимость округления
        if (digitsToRemove > 0 && digits.size() > digitsToRemove) {
            if (digits[digitsToRemove - 1] >= 5) {
                // Округляем вверх
                int carry = 1;
                for (int i = digitsToRemove; i < digits.size() && carry; i++) {
                    digits[i] += carry;
                    if (digits[i] >= 10) {
                        digits[i] -= 10;
                        carry = 1;
                    }
                    else {
                        carry = 0;
                    }
                }
                if (carry) {
                    digits.push_back(1);
                }
            }
        }

        // Удаляем лишние цифры
        digits.erase(digits.begin(), digits.begin() + digitsToRemove);
        decimalPoint = precision;
    }
    else if (decimalPoint < precision) {
        // Добавляем нули для увеличения точности
        digits.insert(digits.begin(), precision - decimalPoint, 0);
        decimalPoint = precision;
    }

    removeLeadingZeros();
}

bool BigNumber::isZero() const {
    return digits.size() == 1 && digits[0] == 0;
}

BigNumber BigNumber::abs() const {
    BigNumber r = *this;
    r.negative = false;
    return r;
}

void BigNumber::removeLeadingZeros() {
    // digits LSB-first. Leading zeros are at the end (MSB side)
    while (digits.size() > 1 && digits.back() == 0) digits.pop_back();
    if (digits.empty()) {
        digits = { 0 };
        negative = false;
        decimalPoint = 0;
    }
}

// Utility: trim leading zeros for LSB-first vector (i.e., pop_back zeroes)
void BigNumber::trimLSBVector(std::vector<int>& a) {
    while (a.size() > 1 && a.back() == 0) a.pop_back();
}

// Align decimals by padding LSB side (inserting zeros at begin)
void BigNumber::alignDecimals(BigNumber& other, int& newDecimal) {
    int maxDecimal = std::max(decimalPoint, other.decimalPoint);
    newDecimal = maxDecimal;
    if (decimalPoint < maxDecimal) {
        digits.insert(digits.begin(), maxDecimal - decimalPoint, 0);
        decimalPoint = maxDecimal;
    }
    if (other.decimalPoint < maxDecimal) {
        other.digits.insert(other.digits.begin(), maxDecimal - other.decimalPoint, 0);
        other.decimalPoint = maxDecimal;
    }
    // equalize overall length
    size_t maxLen = std::max(digits.size(), other.digits.size());
    if (digits.size() < maxLen) digits.resize(maxLen, 0);
    if (other.digits.size() < maxLen) other.digits.resize(maxLen, 0);
}

// ------------------ Простые операции над массивами ------------------

std::vector<int> BigNumber::addArrays(const std::vector<int>& a, const std::vector<int>& b) const {
    std::vector<int> res;
    int carry = 0;
    size_t n = std::max(a.size(), b.size());
    for (size_t i = 0; i < n || carry; ++i) {
        int s = carry;
        if (i < a.size()) s += a[i];
        if (i < b.size()) s += b[i];
        res.push_back(s % 10);
        carry = s / 10;
    }
    trimLSBVector(res);
    return res;
}

std::vector<int> BigNumber::subtractArrays(const std::vector<int>& a, const std::vector<int>& b) const {
    // assume a >= b
    std::vector<int> res(a);
    int borrow = 0;
    for (size_t i = 0; i < res.size(); ++i) {
        int sub = res[i] - borrow - (i < b.size() ? b[i] : 0);
        if (sub < 0) {
            sub += 10;
            borrow = 1;
        }
        else borrow = 0;
        res[i] = sub;
    }
    trimLSBVector(res);
    return res;
}

std::vector<int> BigNumber::multiplyArrays(const std::vector<int>& a, const std::vector<int>& b) const {
    std::vector<int> res(a.size() + b.size(), 0);
    for (size_t i = 0; i < a.size(); ++i) {
        int carry = 0;
        for (size_t j = 0; j < b.size() || carry; ++j) {
            long long cur = res[i + j] + (long long)a[i] * (j < b.size() ? b[j] : 0) + carry;
            res[i + j] = (int)(cur % 10);
            carry = (int)(cur / 10);
        }
    }
    trimLSBVector(res);
    return res;
}

// ------------------ Деление на одну цифру ------------------

void BigNumber::divideByDigit(int digit) {
    if (digit == 1 || isZero()) return;
    if (digit == 0) throw std::runtime_error("Division by zero in divideByDigit");

    std::vector<int> res(digits.size(), 0);
    int rem = 0;
    for (int i = (int)digits.size() - 1; i >= 0; --i) {
        int cur = rem * 10 + digits[i];
        res[i] = cur / digit;
        rem = cur % digit;
    }
    // remove leading zeros (MSB) -> pop_back for LSB-first
    while (res.size() > 1 && res.back() == 0) res.pop_back();
    digits.swap(res);
    removeLeadingZeros();
    // note: remainder rem is lost; if needed, change signature to return it
}

// ------------------ Сравнения ------------------

int BigNumber::compareArrays(const std::vector<int>& a, const std::vector<int>& b) const {
    if (a.size() > b.size()) return 1;
    if (a.size() < b.size()) return -1;
    for (int i = (int)a.size() - 1; i >= 0; --i) {
        if (a[i] > b[i]) return 1;
        if (a[i] < b[i]) return -1;
    }
    return 0;
}

int BigNumber::compare(const BigNumber& other) const {
    if (!negative && other.negative) return 1;
    if (negative && !other.negative) return -1;

    BigNumber a = *this;
    BigNumber b = other;
    int newDec = 0;
    a.alignDecimals(b, newDec);
    int cmp = compareArrays(a.digits, b.digits);
    if (negative && other.negative) return -cmp;
    return cmp;
}

// ------------------ Multiplication ------------------

void BigNumber::multiplyByDigit(int digit) {
    if (digit == 1 || isZero()) return;
    if (digit == 0) { digits = { 0 }; negative = false; decimalPoint = 0; return; }
    std::vector<int> res;
    int carry = 0;
    for (size_t i = 0; i < digits.size() || carry; ++i) {
        long long cur = carry + (i < digits.size() ? (long long)digits[i] * digit : 0);
        res.push_back((int)(cur % 10));
        carry = (int)(cur / 10);
    }
    digits.swap(res);
    removeLeadingZeros();
}

bool BigNumber::isNormalized() const {
    if (isZero()) return true;
    return digits.back() >= 5;
}

// ------------------ DIVISION: helper long division on decimal strings ------------------

// Compare decimal strings (no leading zeros expected, but handle)
static int cmpStrNum(const std::string& a, const std::string& b) {
    std::string aa = a; std::string bb = b;
    // trim leading zeros
    size_t pa = aa.find_first_not_of('0');
    if (pa == std::string::npos) aa = "0"; else aa = aa.substr(pa);
    size_t pb = bb.find_first_not_of('0');
    if (pb == std::string::npos) bb = "0"; else bb = bb.substr(pb);
    if (aa.size() != bb.size()) return aa.size() < bb.size() ? -1 : 1;
    if (aa == bb) return 0;
    return aa < bb ? -1 : 1;
}

static std::string subtractStr(const std::string& a, const std::string& b) {
    // assume a >= b, both non-negative decimal strings MSB-first
    std::string A = a;
    std::string B = std::string(a.size() - b.size(), '0') + b; // pad left
    int n = (int)A.size();
    std::string res(n, '0');
    int carry = 0;
    for (int i = n - 1; i >= 0; --i) {
        int da = A[i] - '0';
        int db = B[i] - '0';
        int cur = da - db - carry;
        if (cur < 0) { cur += 10; carry = 1; }
        else carry = 0;
        res[i] = char('0' + cur);
    }
    // trim leading zeros
    size_t pos = res.find_first_not_of('0');
    if (pos == std::string::npos) return "0";
    return res.substr(pos);
}

static std::string mulStrDigit(const std::string& s, int d) {
    if (d == 0) return "0";
    if (d == 1) {
        // trim leading zeros
        size_t pos = s.find_first_not_of('0');
        if (pos == std::string::npos) return "0";
        return s.substr(pos);
    }
    int n = (int)s.size();
    std::string res;
    int carry = 0;
    for (int i = n - 1; i >= 0; --i) {
        int cur = (s[i] - '0') * d + carry;
        res.push_back(char('0' + (cur % 10)));
        carry = cur / 10;
    }
    while (carry) {
        res.push_back(char('0' + (carry % 10)));
        carry /= 10;
    }
    std::reverse(res.begin(), res.end());
    size_t pos = res.find_first_not_of('0');
    if (pos == std::string::npos) return "0";
    return res.substr(pos);
}

std::string BigNumber::longDivStrings(const std::string& dividend, const std::string& divisor) {
    if (divisor == "0") throw std::runtime_error("Division by zero in string division");
    std::string A = dividend;
    std::string B = divisor;
    // trim leading zeros
    size_t pa = A.find_first_not_of('0'); if (pa == std::string::npos) A = "0"; else A = A.substr(pa);
    size_t pb = B.find_first_not_of('0'); if (pb == std::string::npos) B = "0"; else B = B.substr(pb);

    if (cmpStrNum(A, B) < 0) return "0";

    std::string result;
    std::string cur; // current remainder string
    for (size_t i = 0; i < A.size(); ++i) {
        cur.push_back(A[i]);
        // remove leading zeros
        size_t p = cur.find_first_not_of('0'); if (p == std::string::npos) cur = "0"; else if (p > 0) cur = cur.substr(p);
        // find digit q such that B*q <= cur < B*(q+1)
        int q = 0;
        // binary search 0..9 or simple loop 0..9 is fine
        int low = 0, high = 9;
        while (low <= high) {
            int mid = (low + high) / 2;
            std::string prod = mulStrDigit(B, mid);
            int c = cmpStrNum(prod, cur);
            if (c <= 0) {
                q = mid;
                low = mid + 1;
            }
            else {
                high = mid - 1;
            }
        }
        result.push_back(char('0' + q));
        if (q != 0) {
            std::string prod = mulStrDigit(B, q);
            cur = subtractStr(cur, prod);
        }
    }
    // trim leading zeros of result
    size_t pr = result.find_first_not_of('0');
    if (pr == std::string::npos) return "0";
    return result.substr(pr);
}

// ------------------ Основной метод деления ------------------

// Удаляет нули в дробной части (digits LSB-first, decimalPoint = число цифр после запятой)
static void trimFractionalZeros(std::vector<int>& digits, int& decimalPoint) {
    // fractional digits are digits[0..decimalPoint-1]
    while (decimalPoint > 0 && !digits.empty() && digits[0] == 0) {
        // удалить младший разряд (он же край дробной части)
        digits.erase(digits.begin());
        decimalPoint--;
    }
    // если после удаления дробной части вектор пуст — оставить один ноль
    if (digits.empty()) {
        digits.push_back(0);
        decimalPoint = 0;
    }
    // если decimalPoint == 0, оставляем целую часть как есть
}

BigNumber BigNumber::divide(const BigNumber& other, int precision) const {
    if (other.isZero()) throw std::runtime_error("Division by zero");
    if (isZero()) return BigNumber("0");

    // Быстрые пути
    if (other.digits.size() == 1 && other.digits[0] == 1 && other.decimalPoint == 0) {
        BigNumber r = *this;
        r.negative = (negative != other.negative);
        return r;
    }

    // Вызов устойчивой реализации (divideKnuth)
    BigNumber result = divideKnuth(other, precision);
    result.negative = (negative != other.negative);
    return result;
}


BigNumber BigNumber::divideKnuth(const BigNumber& other, int precision) const {
    if (other.isZero()) throw std::runtime_error("Division by zero");
    if (isZero()) return BigNumber("0");

    // Helper: convert LSB-first vector to MSB-first string
    auto vecToStringMSB = [](const std::vector<int>& v)->std::string {
        std::string s;
        for (int i = (int)v.size() - 1; i >= 0; --i) s.push_back(char('0' + v[i]));
        if (s.empty()) s = "0";
        // trim leading zeros
        size_t p = s.find_first_not_of('0');
        if (p == std::string::npos) return "0";
        return s.substr(p);
        };

    std::string sA = vecToStringMSB(this->digits);   // A_int as string (no decimal point)
    std::string sB = vecToStringMSB(other.digits);  // B_int as string

    // compute scale = precision + db - da
    long long scale = (long long)precision + (long long)other.decimalPoint - (long long)this->decimalPoint;

    if (sA == "0") {
        // Zero divided by anything
        return BigNumber("0");
    }

    if (scale >= 0) {
        // multiply A_int by 10^scale -> append 'scale' zeros to right
        sA.append((size_t)scale, '0');
    }
    else {
        // scale < 0: we need to divide A_int by 10^{-scale} (truncate LSB digits)
        size_t cut = (size_t)(-scale);
        if (cut >= sA.size()) {
            sA = "0";
        }
        else {
            // remove rightmost 'cut' characters
            sA.erase(sA.size() - cut);
            // trim leading zeros
            size_t p = sA.find_first_not_of('0');
            if (p == std::string::npos) sA = "0"; else if (p > 0) sA = sA.substr(p);
        }
    }

    // Now integer divide sA / sB using the existing string long-division helper
    std::string qStr = longDivStrings(sA, sB); // returns "0" .. "..." no leading zeros

    // Ensure qStr has at least precision+1 digits so we can place decimal point;
    // but we already used scale to incorporate decimalPoint differences, so decimalPoint=resultPrecision
    if ((int)qStr.size() <= precision) {
        qStr = std::string(precision + 1 - qStr.size(), '0') + qStr;
    }

    // Convert qStr (MSB-first) into LSB-first digits vector
    std::vector<int> resDigits;
    for (int i = (int)qStr.size() - 1; i >= 0; --i) resDigits.push_back(qStr[i] - '0');

    int resDecimalPoint = precision;

    // Trim redundant fractional zeros (user expects "0.1" not "0.100000...")
    trimFractionalZeros(resDigits, resDecimalPoint);

    BigNumber res(resDigits, (negative != other.negative), resDecimalPoint);
    res.removeLeadingZeros();
    return res;
}

// Fallback simple division via double (kept but not used in main code)
BigNumber BigNumber::divideSimple(const BigNumber& other, int precision) const {
    try {
        double num1 = std::stod(this->toString());
        double num2 = std::stod(other.toString());
        if (num2 == 0.0) throw std::runtime_error("Division by zero");
        double val = num1 / num2;
        std::stringstream ss;
        ss << std::fixed << std::setprecision(precision) << val;
        return BigNumber(ss.str());
    }
    catch (...) {
        throw std::runtime_error("Simple division failed");
    }
}

// ------------------ Простейшие операции: add/subtract/multiply ------------------

BigNumber BigNumber::add(const BigNumber& other) const {
    // sign handling simplified
    if (negative == other.negative) {
        BigNumber a = *this;
        BigNumber b = other;
        int newDec = 0;
        a.alignDecimals(b, newDec);
        std::vector<int> res = addArrays(a.digits, b.digits);
        BigNumber r(res, negative, newDec);
        r.removeLeadingZeros();
        return r;
    }
    else {
        // a + (-b) => a - b
        if (negative) {
            BigNumber ta = *this; ta.negative = false;
            return other.subtract(ta);
        }
        else {
            BigNumber tb = other; tb.negative = false;
            return this->subtract(tb);
        }
    }
}

BigNumber BigNumber::subtract(const BigNumber& other) const {
    // sign handling omitted full details for brevity (keeps previous behavior)
    if (negative != other.negative) {
        BigNumber tmp = other;
        tmp.negative = !tmp.negative;
        return this->add(tmp);
    }
    // both same sign: compute absolute comparison
    BigNumber a = *this;
    BigNumber b = other;
    int newDec = 0;
    a.alignDecimals(b, newDec);
    int cmp = compareArrays(a.digits, b.digits);
    std::vector<int> resDigits;
    bool resNeg = false;
    if (cmp >= 0) {
        resDigits = subtractArrays(a.digits, b.digits);
        resNeg = negative;
    }
    else {
        resDigits = subtractArrays(b.digits, a.digits);
        resNeg = !negative;
    }
    BigNumber r(resDigits, resNeg, newDec);
    r.removeLeadingZeros();
    return r;
}

BigNumber BigNumber::multiply(const BigNumber& other) const {
    int resDec = decimalPoint + other.decimalPoint;
    std::vector<int> resDigits = multiplyArrays(digits, other.digits);
    BigNumber r(resDigits, (negative != other.negative), resDec);
    r.removeLeadingZeros();
    return r;
}

BigNumber BigNumber::factorial() const {
    if (negative) {
        throw std::runtime_error("Factorial of negative number is undefined.");
    }
    if (decimalPoint > 0) {
        throw std::runtime_error("Factorial of fractional number is undefined.");
    }

    // Handle 0! = 1 and 1! = 1
    if (isZero() || compare(BigNumber("1")) == 0) {
        return BigNumber("1");
    }

    BigNumber result("1");
    BigNumber counter("1");
    BigNumber one("1");

    // Iterate from 1 up to this number
    while (counter.compare(*this) <= 0) {
        result = result * counter;
        counter = counter + one;
    }

    return result;
}

// helper: check if |a - b| < 10^{-precision}
static bool isCloseAtPrecision(const BigNumber& a, const BigNumber& b, int precision) {
    BigNumber diff = a - b;
    if (diff.negative) diff = diff.abs();
    // build threshold: "0." followed by (precision) zeros then "1" -> 10^{-(precision)}
    std::string thr = "0.";
    for (int i = 1; i < precision; ++i) thr.push_back('0');
    thr.push_back('1'); // now thr = 0.00...01 with precision digits after dot
    // if precision==0 then threshold is "1"
    if (precision == 0) thr = "1";
    BigNumber threshold(thr);
    return diff.compare(threshold) < 0;
}

// helper: number of integer digits (approx), based on digits and decimalPoint
static int integerDigits(const BigNumber& x) {
    int total = (int)x.getDigits().size();
    int frac = x.getDecimalPoint();
    int intDigits = total - frac;
    if (intDigits <= 0) return 1; // numbers < 1 -> count as 1 digit (for approximation)
    return intDigits;
}


// ------------------ Вычисление ln(2) с высокой точностью ------------------

BigNumber BigNumber::compute_ln2(int precision) {
    // Используем ряд: ln(2) = 2 * [ (1/3) + (1/3)^3/3 + (1/3)^5/5 + ... ]
    // Этот ряд сходится быстро и не требует рекурсии
    BigNumber one("1");
    BigNumber three("3");
    BigNumber two("2");

    BigNumber y = one.divide(three, precision + 10);
    BigNumber y_sq = y * y;
    BigNumber term = y;
    BigNumber sum = term;

    int max_iterations = 100;
    for (int n = 3; n <= max_iterations * 2; n += 2) {
        term = term * y_sq;
        BigNumber current_term = term.divide(BigNumber(std::to_string(n)), precision + 10);

        if (current_term.isZero()) {
            break;
        }

        sum = sum + current_term;
    }

    return sum * two;
}

// ------------------ Вычисление ln(10) с высокой точностью ------------------

BigNumber BigNumber::compute_ln10(int precision) {
    // ln(10) = ln(2) + ln(5)
    BigNumber ln2 = compute_ln2(precision + 5);
    BigNumber five("5");
    BigNumber ln5 = five.ln_direct(precision + 5);

    return ln2 + ln5;
}

// ------------------ Прямое вычисление ln без рекурсии ------------------

BigNumber BigNumber::ln_direct(int precision) const {
    if (negative || isZero()) {
        throw std::runtime_error("Natural log of non-positive number");
    }

    BigNumber one("1");
    BigNumber two("2");
    BigNumber half("0.5");

    if (this->compare(one) == 0) {
        return BigNumber("0");
    }

    // Нормализуем число к диапазону [0.5, 2]
    BigNumber x = *this;
    int k = 0;

    // Если число > 2, делим на 2
    while (x.compare(two) > 0) {
        x = x.divide(two, precision + 10);
        k++;
    }

    // Если число < 0.5, умножаем на 2
    while (x.compare(half) < 0) {
        x = x * two;
        k--;
    }

    // Вычисляем ln(normalized_x) используя ряд Тейлора
    BigNumber y = (x - one).divide(x + one, precision + 10);
    BigNumber y_sq = y * y;
    BigNumber term = y;
    BigNumber sum = term;

    int max_iterations = 100;
    for (int n = 3; n <= max_iterations * 2; n += 2) {
        term = term * y_sq;
        BigNumber current_term = term.divide(BigNumber(std::to_string(n)), precision + 10);

        if (current_term.isZero()) {
            break;
        }

        sum = sum + current_term;
    }

    BigNumber ln_x = sum * two;

    // Используем предварительно вычисленный ln(2)
    BigNumber ln2 = compute_ln2(precision + 5);

    // ln(original) = k * ln(2) + ln(normalized_x)
    BigNumber k_ln2 = ln2 * BigNumber(std::to_string(k));
    BigNumber result = k_ln2 + ln_x;

    result.setPrecision(precision);
    return result;
}

// ------------------ Основная реализация ln ------------------

BigNumber BigNumber::ln(int precision) const {
    return ln_direct(precision);
}

// ------------------ Реализация log10 ------------------

BigNumber BigNumber::log10(int precision) const {
    if (negative || isZero()) {
        throw std::runtime_error("Log10 of non-positive number");
    }

    // Явная обработка специальных случаев чтобы избежать ошибок округления, НАДО ПЕРЕДЕЛАТЬ
    BigNumber one("1");
    BigNumber ten("10");
    BigNumber zero_point_one("0.1");
    BigNumber zero_point_zero_one("0.01");
    BigNumber zero_point_zero_zero_one("0.001");

    if (this->compare(one) == 0) {
        return BigNumber("0");
    }
    else if (this->compare(ten) == 0) {
        return BigNumber("1");
    }
    else if (this->compare(zero_point_one) == 0) {
        return BigNumber("-1");
    }
    else if (this->compare(zero_point_zero_one) == 0) {
        return BigNumber("-2");
    }
    else if (this->compare(zero_point_zero_zero_one) == 0) {
        return BigNumber("-3");
    }

    // Используем повышенную точность для промежуточных вычислений
    int intermediate_precision = precision + 20;
    BigNumber ln_x = this->ln_direct(intermediate_precision);
    BigNumber ln_10 = compute_ln10(intermediate_precision);

    BigNumber result = ln_x.divide(ln_10, intermediate_precision);
    result.setPrecision(precision);
    return result;
}

// ------------------ Упрощенная реализация exp ------------------

BigNumber BigNumber::exp(int precision) const {
    if (isZero()) {
        return BigNumber("1");
    }

    if (negative) {
        BigNumber pos = this->abs();
        BigNumber exp_pos = pos.exp(precision + 5);
        return BigNumber("1").divide(exp_pos, precision);
    }

    // Упрощенный ряд Тейлора для exp(x)
    BigNumber one("1");
    BigNumber result("1");
    BigNumber term("1");
    BigNumber x = *this;

    int max_iterations = 50;
    for (int i = 1; i < max_iterations; i++) {
        term = term * x;
        term = term.divide(BigNumber(std::to_string(i)), precision + 10);

        if (term.isZero()) {
            break;
        }

        result = result + term;
    }

    result.setPrecision(precision);
    return result;
}

// ------------------ Упрощенная реализация power ------------------

BigNumber BigNumber::power(const BigNumber& exponent, int precision) const {
    if (this->isZero()) {
        if (exponent.isZero()) {
            throw std::runtime_error("0^0 is undefined");
        }
        return BigNumber("1");
    }

    // Целые показатели степени
    if (exponent.decimalPoint == 0 && !exponent.negative) {
        BigNumber result("1");
        BigNumber base = *this;
        BigNumber exp = exponent;

        while (!exp.isZero()) {
            if (exp.digits[0] % 2 == 1) {
                result = result * base;
            }
            base = base * base;
            exp = exp.divide(BigNumber("2"), 0);
        }
        return result;
    }

    // Отрицательные целые показатели
    if (exponent.decimalPoint == 0 && exponent.negative) {
        BigNumber positive_exp = exponent;
        positive_exp.negative = false;
        BigNumber result = this->power(positive_exp);
        return BigNumber("1").divide(result, 30);
    }

    // Дробные показатели: x^y = exp(y * ln(x))
    if (this->negative) {
        throw std::runtime_error("Negative base with fractional exponent is undefined in real numbers");
    }

    // Используем умеренную точность для избежания переполнения
    BigNumber ln_x = this->ln_direct(30);
    BigNumber y_ln_x = exponent * ln_x;
    return y_ln_x.exp(30);
}

// ------------------ Вспомогательные методы ------------------

BigNumber BigNumber::negate() const {
    BigNumber result = *this;
    result.negative = !result.negative;
    return result;
}

BigNumber BigNumber::operator-() const {
    return this->negate();
}

// ------------------ Улучшенная редукция углов ------------------

BigNumber BigNumber::mod2Pi(int precision) const {
    BigNumber twoPi = BigNumber::pi(precision + 30) * BigNumber("2");
    BigNumber x = *this;

    // Для отрицательных углов
    if (x.negative) {
        BigNumber absX = x.abs();
        BigNumber quotient = absX.divide(twoPi, 0);
        BigNumber remainder = absX - (quotient * twoPi);
        if (!remainder.isZero()) {
            remainder = twoPi - remainder;
        }
        return remainder;
    }

    // Для положительных углов
    BigNumber quotient = x.divide(twoPi, 0);
    return x - (quotient * twoPi);
}

// ------------------ Вспомогательные функции для редукции ------------------

void BigNumber::reduceToFirstQuadrant(const BigNumber& x, BigNumber& reducedX, int& quadrant, int precision) {
    BigNumber pi = BigNumber::pi(precision + 20);
    BigNumber twoPi = pi * BigNumber("2");
    BigNumber piHalf = pi.divide(BigNumber("2"), precision + 20);

    // Вычисляем x mod 2π вручную (без вызова метода mod2Pi)
    BigNumber quotient = x.divide(twoPi, 0); // целочисленное деление
    BigNumber modX = x - (quotient * twoPi);

    // Обеспечиваем неотрицательность
    if (modX.negative) {
        modX = modX + twoPi;
    }

    // Определяем квадрант
    if (modX.compare(piHalf) <= 0) {
        quadrant = 1;
        reducedX = modX;
    }
    else if (modX.compare(pi) <= 0) {
        quadrant = 2;
        reducedX = pi - modX;
    }
    else if (modX.compare(piHalf * BigNumber("3")) <= 0) {
        quadrant = 3;
        reducedX = modX - pi;
    }
    else {
        quadrant = 4;
        reducedX = twoPi - modX;
    }
}

// helper: create BigNumber threshold 10^{-n} where n >= 0
static BigNumber makePow10Neg(int n) {
    if (n <= 0) return BigNumber("1");
    std::string s = "0.";
    for (int i = 1; i < n; ++i) s.push_back('0');
    s.push_back('1');
    return BigNumber(s);
}

// ------------------ Высокоточные ряды Тейлора для малых углов ------------------

BigNumber BigNumber::sin_taylor_small(const BigNumber& x, int precision) const {
    // precision — желаемое количество дробных цифр результата (без guard)
    if (x.isZero()) return BigNumber("0");

    // Если угол очень мал, использовать приближение x - x^3/6
    BigNumber smallThreshold("0.01");
    if (x.compare(smallThreshold) < 0) {
        BigNumber x3 = x * x * x;
        return x - x3.divide(BigNumber("6"), precision + 8);
    }

    int guard = std::max(16, precision + 40); // защитные цифры
    BigNumber xSquared = x * x;
    BigNumber term = x;            // x^(2n+1) / (2n+1) starts with x
    BigNumber result = term;

    BigNumber threshold = makePow10Neg(precision + 8);

    // iterative series: term_{n+1} = term_n * x^2 / ((2n)*(2n+1))
    for (int n = 1; n < 10000; ++n) {
        term = term * xSquared;
        BigNumber denom(std::to_string((2 * n) * (2 * n + 1)));
        term = term.divide(denom, guard);

        BigNumber termAbs = term.isNegative() ? term.abs() : term;
        if (termAbs.compare(threshold) <= 0) break;

        if (n % 2 == 0) result = result + term; else result = result - term;
    }

    // final rounding to requested precision
    result.setPrecision(precision + 2);
    return result;
}

BigNumber BigNumber::cos_taylor_small(const BigNumber& x, int precision) const {
    if (x.isZero()) return BigNumber("1");

    BigNumber smallThreshold("0.01");
    if (x.compare(smallThreshold) < 0) {
        BigNumber x2 = x * x;
        return BigNumber("1") - x2.divide(BigNumber("2"), precision + 8);
    }

    int guard = std::max(16, precision + 40);
    BigNumber xSquared = x * x;
    BigNumber term("1"); // starts as 1
    BigNumber result = term;

    BigNumber threshold = makePow10Neg(precision + 8);

    // term_{n+1} = term_n * x^2 / ((2n-1)*(2n))
    for (int n = 1; n < 10000; ++n) {
        term = term * xSquared;
        BigNumber denom(std::to_string((2 * n - 1) * (2 * n)));
        term = term.divide(denom, guard);

        BigNumber termAbs = term.isNegative() ? term.abs() : term;
        if (termAbs.compare(threshold) <= 0) break;

        if (n % 2 == 0) result = result + term; else result = result - term;
    }

    result.setPrecision(precision + 2);
    return result;
}


// ------------------ Основные реализации sin и cos ------------------

BigNumber BigNumber::sin(int precision) const {


    // Специальные случаи
    if (this->isZero()) return BigNumber("0");

    // Редукция до первого квадранта
    BigNumber reducedX;
    int quadrant;
    const_cast<BigNumber*>(this)->reduceToFirstQuadrant(*this, reducedX, quadrant, precision);

    // Если угол уже мал, используем ряд Тейлора
    BigNumber threshold("0.5");
    if (reducedX.compare(threshold) <= 0) {
        BigNumber result = sin_taylor_small(reducedX, precision);
        return (quadrant == 3 || quadrant == 4) ? result.negate() : result;
    }

    // Редукция половинного угла
    int reductions = 0;
    BigNumber x = reducedX;
    while (x.compare(threshold) > 0) {
        x = x.divide(BigNumber("2"), precision + 20);
        reductions++;
    }

    // Вычисляем sin и cos для малого угла
    BigNumber sinX = sin_taylor_small(x, precision + 10);
    BigNumber cosX = cos_taylor_small(x, precision + 10);

    // Применяем формулы двойного угла
    for (int i = 0; i < reductions; i++) {
        BigNumber newSin = (sinX * cosX) * BigNumber("2");
        BigNumber newCos = (cosX * cosX) * BigNumber("2") - BigNumber("1");
        sinX = newSin;
        cosX = newCos;
    }

    // Корректируем знак по квадранту
    return (quadrant == 3 || quadrant == 4) ? sinX.negate() : sinX;
}

BigNumber BigNumber::cos(int precision) const {

    // Специальные случаи
    if (this->isZero()) return BigNumber("1");

    // Редукция до первого квадранта
    BigNumber reducedX;
    int quadrant;
    const_cast<BigNumber*>(this)->reduceToFirstQuadrant(*this, reducedX, quadrant, precision);

    // Если угол уже мал, используем ряд Тейлора
    BigNumber threshold("0.5");
    if (reducedX.compare(threshold) <= 0) {
        BigNumber result = cos_taylor_small(reducedX, precision);
        return (quadrant == 2 || quadrant == 3) ? result.negate() : result;
    }

    // Редукция половинного угла
    int reductions = 0;
    BigNumber x = reducedX;
    while (x.compare(threshold) > 0) {
        x = x.divide(BigNumber("2"), precision + 20);
        reductions++;
    }

    // Вычисляем sin и cos для малого угла
    BigNumber sinX = sin_taylor_small(x, precision + 10);
    BigNumber cosX = cos_taylor_small(x, precision + 10);

    // Применяем формулы двойного угла
    for (int i = 0; i < reductions; i++) {
        BigNumber newSin = (sinX * cosX) * BigNumber("2");
        BigNumber newCos = (cosX * cosX) * BigNumber("2") - BigNumber("1");
        sinX = newSin;
        cosX = newCos;
    }

    // Корректируем знак по квадранту
    return (quadrant == 2 || quadrant == 3) ? cosX.negate() : cosX;
}

// ------------------ Улучшенная реализация tan ------------------

BigNumber BigNumber::tan(int precision) const {
    BigNumber sinVal = this->sin();
    BigNumber cosVal = this->cos();

    if (cosVal.isZero()) {
        throw std::runtime_error("Tangent undefined");
    }

    return sinVal.divide(cosVal, precision);
}

// ------------------ Высокоточное вычисление π ------------------

// ------------------ Helper: arctan series (MSB-friendly, stable) ------------------
// Computes arctan(x) for 0 < x <= 1 using series: arctan(x) = sum_{n>=0} (-1)^n * x^(2n+1)/(2n+1)
// x is passed as BigNumber (like 1/5). precision = number of fractional digits required.
static BigNumber arctan_series(const BigNumber& x, int precision) {
    // guard digits to reduce rounding accumulation
    int guard = std::max(16, precision / 6 + 16);

    BigNumber x_pow = x;              // x^(2n+1), starts with x^1
    BigNumber x2 = x * x;             // x^2
    BigNumber sum = x_pow;            // first term
    BigNumber term = x_pow;
    BigNumber one("1");

    // threshold: 10^{-(precision+guard)}
    std::string thr = "0.";
    for (int i = 1; i < precision + guard; ++i) thr.push_back('0');
    thr.push_back('1');
    BigNumber threshold(thr);

    for (int n = 1;; ++n) {
        // prepare next power: multiply by x^2
        term = term * x2; // now term = x^(2n+1)
        // denom = 2n+1
        BigNumber denom(std::to_string(2 * n + 1));
        BigNumber add = term.divide(denom, precision + guard);

        // alternating sign
        if (n % 2 == 1) {
            sum = sum - add;
        }
        else {
            sum = sum + add;
        }

        BigNumber addAbs = add;
        if (addAbs.negative) addAbs = addAbs.abs();
        if (addAbs.compare(threshold) <= 0) break;

        // safety cap (should never hit for reasonable precision)
        if (n > (precision + guard) * 50) break;
    }

    return sum;
}

// ------------------ New implementation of pi using Machin formula ------------------
// π = 16*arctan(1/5) - 4*arctan(1/239)
BigNumber BigNumber::pi(int precision) {
    if (precision < 2) precision = 2;
    // compute x1 = 1/5 and x2 = 1/239 with sufficient guard
    int guard = std::max(20, precision / 4 + 20);
    BigNumber one("1");
    BigNumber five("5");
    BigNumber twoThreeNine("239");

    BigNumber x1 = one.divide(five, precision + guard);         // 1/5
    BigNumber x2 = one.divide(twoThreeNine, precision + guard); // 1/239

    BigNumber ar1 = arctan_series(x1, precision);
    BigNumber ar2 = arctan_series(x2, precision);

    BigNumber part1 = ar1 * BigNumber("16");
    BigNumber part2 = ar2 * BigNumber("4");

    BigNumber pi_val = part1 - part2;
    pi_val.setPrecision(precision);
    return pi_val;
}



BigNumber BigNumber::e(int precision) {
    // Ряд Тейлора для e = 1 + 1 + 1/2! + 1/3! + ...
    BigNumber result("1");
    BigNumber term("1");

    int max_iterations = 50;
    for (int i = 1; i < max_iterations; i++) {
        term = term.divide(BigNumber(std::to_string(i)), precision + 10);

        if (term.isZero()) {
            break;
        }

        result = result + term;
    }

    return result;
}

std::string BigNumber::debugString() const {
    std::stringstream ss;
    ss << "BigNumber{ value: '" << toString() << "', negative: " << negative << ", decimalPoint: " << decimalPoint << ", digits: [";
    for (size_t i = 0; i < digits.size(); ++i) {
        if (i) ss << ",";
        ss << digits[i];
    }
    ss << "] }";
    return ss.str();
}


// ------------------ Improved Calculator with caching and precision ------------------

Calculator::Calculator(Logger* logger_, int precision_)
    : logger(logger_), precision(precision_) {}

void Calculator::setPrecision(int newPrecision) {
    if (newPrecision != precision) {
        precision = newPrecision;
        // Очищаем кэш при изменении точности
        cache.clear();
    }
}

void Calculator::log(const std::string& level, const std::string& message) {
    if (logger) logger->log(level, message);
}

BigNumber Calculator::evaluate(const std::string& expression) {
    log("INFO", "Evaluating: " + expression + " with precision: " + std::to_string(precision));

    auto tokens = tokenize(expression);
    size_t index = 0;

    // Используем кэшированную версию вычисления
    BigNumber result = evaluateWithCache(expression, tokens, 0, tokens.size());

    log("INFO", "Result: " + result.toString());
    return result;
}

BigNumber Calculator::evaluateWithCache(const std::string& expression, const std::vector<std::string>& tokens, size_t start, size_t end) {
    // Создаем ключ для кэша
    std::string subExpr = getSubExpression(tokens, start, end);
    CacheKey key{subExpr, precision};

    // Проверяем кэш
    auto cached = cache.find(key);
    if (cached != cache.end()) {
        log("DEBUG", "Cache hit for: " + key.expression);
        return cached->second;
    }

    // Вычисляем выражение
    size_t index = start;
    BigNumber result = parseExpression(tokens, index);

    // Сохраняем в кэш
    cache[key] = result;
    log("DEBUG", "Cached result for: " + key.expression);

    return result;
}

std::string Calculator::getSubExpression(const std::vector<std::string>& tokens, size_t start, size_t end) {
    std::string result;
    for (size_t i = start; i < end && i < tokens.size(); ++i) {
        if (!result.empty()) result += " ";
        result += tokens[i];
    }
    return result;
}

std::vector<std::string> Calculator::tokenize(const std::string& expression) {
    std::vector<std::string> tokens;
    std::string current;
    for (char c : expression) {
        if (isspace((unsigned char)c)) {
            if (!current.empty()) { tokens.push_back(current); current.clear(); }
        }
        else if (c == '(' || c == ')' || c == '+' || c == '-' || c == '*' || c == '/' || c == '^' || c == '!' || c == ',') {
            if (!current.empty()) { tokens.push_back(current); current.clear(); }
            tokens.push_back(std::string(1, c));
        }
        else {
            current += c;
        }
    }
    if (!current.empty()) tokens.push_back(current);
    return tokens;
}

BigNumber Calculator::parseExpression(const std::vector<std::string>& tokens, size_t& index) {
    BigNumber res = parseTerm(tokens, index);
    while (index < tokens.size()) {
        std::string op = tokens[index];
        if (op == "+" || op == "-") {
            index++;
            BigNumber right = parseTerm(tokens, index);
            if (op == "+") {
                res = res + right;
            } else {
                res = res - right;
            }
        }
        else break;
    }
    return res;
}

BigNumber Calculator::parseTerm(const std::vector<std::string>& tokens, size_t& index) {
    BigNumber res = parseFactor(tokens, index);
    while (index < tokens.size()) {
        std::string op = tokens[index];
        if (op == "*" || op == "/") {
            index++;
            BigNumber right = parseFactor(tokens, index);
            if (op == "*") {
                res = res * right;
            } else {
                res = res.divide(right, precision);
            }
        }
        else break;
    }
    return res;
}

BigNumber Calculator::parseFactor(const std::vector<std::string>& tokens, size_t& index) {
    BigNumber res = parseNumber(tokens, index);
    while (index < tokens.size()) {
        std::string op = tokens[index];
        if (op == "^") {
            index++;
            BigNumber exp = parseFactor(tokens, index);
            res = res.power(exp, precision);
        }
        else if (op == "!") {
            index++;
            res = res.factorial();
        }
        else break;
    }
    return res;
}

BigNumber Calculator::parseFunction(const std::string& funcName, const std::vector<std::string>& tokens, size_t& index) {
    if (index >= tokens.size() || tokens[index] != "(") {
        throw std::runtime_error("Expected '(' after function: " + funcName);
    }
    index++; // пропускаем "("

    BigNumber arg = parseExpression(tokens, index);

    if (index >= tokens.size() || tokens[index] != ")") {
        throw std::runtime_error("Expected ')' after function argument: " + funcName);
    }
    index++; // пропускаем ")"

    if (funcName == "sin") return arg.sin(precision);
    else if (funcName == "cos") return arg.cos(precision);
    else if (funcName == "tan") return arg.tan(precision);
    else if (funcName == "ln") return arg.ln(precision);
    else if (funcName == "log") return arg.log10(precision);
    else if (funcName == "exp") return arg.exp(precision);
    else if (funcName == "factorial") return arg.factorial();
    else if (funcName == "sqrt") return arg.power(BigNumber("0.5"), precision);
    else throw std::runtime_error("Unknown function: " + funcName);
}

BigNumber Calculator::parseNumber(const std::vector<std::string>& tokens, size_t& index) {
    if (index >= tokens.size()) throw std::runtime_error("Unexpected end of expression");
    std::string token = tokens[index++];

    // Проверяем кэш для простых выражений
    CacheKey simpleKey{token, precision};
    auto cached = cache.find(simpleKey);
    if (cached != cache.end()) {
        return cached->second;
    }

    if (token == "(") {
        // Для выражений в скобках используем кэширование
        size_t start = index;
        int bracketCount = 1;
        size_t end = index;

        // Находим соответствующую закрывающую скобку
        while (end < tokens.size() && bracketCount > 0) {
            if (tokens[end] == "(") bracketCount++;
            else if (tokens[end] == ")") bracketCount--;
            end++;
        }

        if (bracketCount > 0) throw std::runtime_error("Missing closing parenthesis");

        // Вычисляем выражение в скобках с кэшированием
        BigNumber result = evaluateWithCache("", tokens, start, end - 1);
        index = end;

        // Кэшируем результат выражения в скобках
        std::string subExpr = "(" + getSubExpression(tokens, start, end - 1) + ")";
        cache[CacheKey{subExpr, precision}] = result;

        return result;
    }

    BigNumber result;

    // Обрабатываем функции
    if (token == "sin" || token == "cos" || token == "tan" || token == "ln" || token == "log" ||
        token == "exp" || token == "factorial" || token == "sqrt" || token == "pi" || token == "e") {

        if (token == "pi") {
            result = BigNumber::pi(precision);
        }
        else if (token == "e") {
            result = BigNumber::e(precision);
        }
        else {
            result = parseFunction(token, tokens, index);
        }
    }
    else {
        // Обычное число
        try {
            result = BigNumber(token);
        }
        catch (...) {
            throw std::runtime_error("Invalid number or function: " + token);
        }
    }

    // Кэшируем простой токен
    cache[simpleKey] = result;
    return result;
}
// C interface
extern "C" {
    __declspec(dllexport) Calculator* create_calculator_with_precision(int precision) {
        try {
            return new Calculator(nullptr, precision);
        }
        catch (...) {
            return nullptr;
        }
    }

    __declspec(dllexport) Calculator* create_calculator() {
        return create_calculator_with_precision(50);
    }

    __declspec(dllexport) char* calculate_expression(Calculator* calc, const char* expression) {
        if (!calc || !expression) return nullptr;

        // Буфер для безопасного копирования
        char* result_buffer = nullptr;

        try {
            BigNumber res = calc->evaluate(std::string(expression));
            std::string s = res.toString();

            // Безопасное выделение памяти
            result_buffer = (char*)std::malloc(s.size() + 1);
            if (!result_buffer) return nullptr;

            std::strcpy(result_buffer, s.c_str());
            return result_buffer;
        }
        catch (const std::exception& e) {
            std::string err = std::string("Error: ") + e.what();

            // Освобождаем предыдущий буфер если был
            if (result_buffer) {
                std::free(result_buffer);
                result_buffer = nullptr;
            }

            result_buffer = (char*)std::malloc(err.size() + 1);
            if (!result_buffer) return nullptr;

            std::strcpy(result_buffer, err.c_str());
            return result_buffer;
        }
        catch (...) {
            const char* msg = "Error: Unknown exception";

            if (result_buffer) {
                std::free(result_buffer);
                result_buffer = nullptr;
            }

            result_buffer = (char*)std::malloc(std::strlen(msg) + 1);
            if (!result_buffer) return nullptr;

            std::strcpy(result_buffer, msg);
            return result_buffer;
        }
    }

    __declspec(dllexport) void set_calculator_precision(Calculator* calc, int precision) {
        if (calc) calc->setPrecision(precision);
    }

    __declspec(dllexport) int get_calculator_precision(Calculator* calc) {
        return calc ? calc->getPrecision() : -1;
    }

    __declspec(dllexport) void delete_calculator(Calculator* calc) {
        if (calc) {
            delete calc;
        }
    }

    __declspec(dllexport) void free_result(char* result) {
        if (result) {
            std::free(result);
        }
    }
}
