import socket
import requests
import platform
import subprocess
import re
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError
import json


class IPAddressUtils:
    """Утилита для работы с IP-адресами"""

    @staticmethod
    def get_local_ip() -> str:
        """
        Получает локальный IP-адрес компьютера в сети
        """
        try:
            # Создаем временное соединение чтобы определить IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Подключаемся к публичному DNS серверу
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            # Fallback: получаем IP через hostname
            try:
                return socket.gethostbyname(socket.gethostname())
            except Exception:
                return "127.0.0.1"

    @staticmethod
    def get_all_local_ips() -> List[Dict[str, str]]:
        """
        Получает все локальные IP-адреса всех сетевых интерфейсов
        """
        ips = []
        system = platform.system().lower()

        try:
            if system == 'windows':
                ips = IPAddressUtils._get_windows_ips()
            elif system in ['linux', 'darwin']:  # Linux или Mac
                ips = IPAddressUtils._get_unix_ips()
            else:
                # Универсальный способ
                ips = IPAddressUtils._get_universal_ips()
        except Exception as e:
            print(f"Ошибка получения IP-адресов: {e}")
            # Добавляем хотя бы основной IP
            main_ip = IPAddressUtils.get_local_ip()
            if main_ip and main_ip != "127.0.0.1":
                ips.append({
                    'interface': 'Основной',
                    'ipv4': main_ip,
                    'ipv6': '',
                    'type': 'Основной'
                })

        return ips

    @staticmethod
    def _get_windows_ips() -> List[Dict[str, str]]:
        """Получает IP-адреса в Windows"""
        ips = []
        try:
            # Используем ipconfig
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_interface = ""
                ipv4 = ""
                ipv6 = ""

                for line in lines:
                    line = line.strip()
                    # Ищем название интерфейса
                    if line and not line.startswith(' ') and ':' not in line and not any(
                            x in line for x in ['Windows', 'Configuration']):
                        current_interface = line

                    # Ищем IPv4
                    if 'IPv4 Address' in line or 'IPv4-адрес' in line:
                        match = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', line)
                        if match:
                            ipv4 = match.group()

                    # Ищем IPv6
                    if 'IPv6 Address' in line or 'IPv6-адрес' in line:
                        match = re.search(r'([a-f0-9:]+:+)+[a-f0-9]+', line, re.IGNORECASE)
                        if match:
                            ipv6 = match.group()

                    # Когда находим пустую строку, сохраняем собранные данные
                    if not line and current_interface and (ipv4 or ipv6):
                        interface_type = "Wi-Fi" if "wireless" in current_interface.lower() or "wi-fi" in current_interface.lower() else "Ethernet"
                        if "loopback" in current_interface.lower() or ipv4 == "127.0.0.1":
                            interface_type = "Loopback"

                        ips.append({
                            'interface': current_interface,
                            'ipv4': ipv4,
                            'ipv6': ipv6,
                            'type': interface_type
                        })
                        current_interface = ""
                        ipv4 = ""
                        ipv6 = ""
        except Exception as e:
            print(f"Ошибка получения IP в Windows: {e}")

        return ips

    @staticmethod
    def _get_unix_ips() -> List[Dict[str, str]]:
        """Получает IP-адреса в Linux/Mac"""
        ips = []
        try:
            # Используем ifconfig или ip addr
            commands = [['ip', 'addr'], ['ifconfig']]

            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        current_interface = ""
                        ipv4 = ""
                        ipv6_list = []

                        for line in lines:
                            line = line.strip()

                            # Ищем название интерфейса
                            if line and not line.startswith(' ') and ':' in line and not line.startswith('inet'):
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    current_interface = parts[1].strip() if len(parts) > 1 else parts[0]

                            # Ищем IPv4
                            if line.startswith('inet ') and not line.startswith('inet6'):
                                match = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', line)
                                if match:
                                    ipv4 = match.group()

                            # Ищем IPv6
                            if line.startswith('inet6 '):
                                match = re.search(r'([a-f0-9:]+:+)+[a-f0-9]+', line, re.IGNORECASE)
                                if match and 'fe80' not in match.group():  # Исключаем link-local
                                    ipv6_list.append(match.group())

                            # Сохраняем когда находим пустую строку или новый интерфейс
                            if (not line or (line and not line.startswith(
                                    ' ') and ':' in line and current_interface)) and current_interface and (
                                    ipv4 or ipv6_list):
                                interface_type = "Wi-Fi" if "wl" in current_interface or "wlan" in current_interface else "Ethernet"
                                if "lo" in current_interface or ipv4 == "127.0.0.1":
                                    interface_type = "Loopback"

                                ips.append({
                                    'interface': current_interface,
                                    'ipv4': ipv4,
                                    'ipv6': ', '.join(ipv6_list) if ipv6_list else '',
                                    'type': interface_type
                                })
                                current_interface = ""
                                ipv4 = ""
                                ipv6_list = []

                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"Ошибка получения IP в Unix: {e}")

        return ips

    @staticmethod
    def _get_universal_ips() -> List[Dict[str, str]]:
        """Универсальный способ получения IP-адресов"""
        ips = []
        try:
            # Получаем все сетевые интерфейсы
            for interface in socket.if_nameindex():
                interface_name = interface[1]
                try:
                    # Получаем адреса для интерфейса
                    addresses = socket.getaddrinfo(interface_name, None)
                    ipv4 = ""
                    ipv6_list = []

                    for addr in addresses:
                        ip = addr[4][0]
                        if ':' in ip:  # IPv6
                            if not ip.startswith('fe80'):  # Исключаем link-local
                                ipv6_list.append(ip)
                        else:  # IPv4
                            if not ip.startswith('127.'):  # Исключаем localhost
                                ipv4 = ip

                    if ipv4 or ipv6_list:
                        interface_type = "Wi-Fi" if "wl" in interface_name or "wlan" in interface_name else "Ethernet"
                        if "lo" in interface_name or ipv4 == "127.0.0.1":
                            interface_type = "Loopback"

                        ips.append({
                            'interface': interface_name,
                            'ipv4': ipv4,
                            'ipv6': ', '.join(ipv6_list) if ipv6_list else '',
                            'type': interface_type
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"Ошибка универсального получения IP: {e}")

        return ips

    @staticmethod
    def get_external_ip(timeout: int = 5) -> Dict[str, str]:
        """
        Получает внешний IP-адрес через публичные сервисы

        Args:
            timeout: Таймаут в секундах для каждого запроса

        Returns:
            Словарь с IP-адресом и источником
        """
        services = [
            {
                'name': 'ipify',
                'url': 'https://api.ipify.org',
                'parser': lambda text: text.strip()
            },
            {
                'name': 'icanhazip',
                'url': 'https://icanhazip.com',
                'parser': lambda text: text.strip()
            },
            {
                'name': 'jsonip',
                'url': 'https://jsonip.com',
                'parser': lambda text: json.loads(text)['ip']
            },
            {
                'name': 'httpbin',
                'url': 'https://httpbin.org/ip',
                'parser': lambda text: json.loads(text)['origin']
            }
        ]

        for service in services:
            try:
                response = requests.get(service['url'], timeout=timeout)
                if response.status_code == 200:
                    ip = service['parser'](response.text)
                    if ip and IPAddressUtils._is_valid_ip(ip):
                        return {
                            'ip': ip,
                            'source': service['name'],
                            'type': 'IPv4' if '.' in ip else 'IPv6'
                        }
            except Exception:
                continue

        # Fallback: пытаемся получить через socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                external_ip = s.getsockname()[0]
                return {
                    'ip': external_ip,
                    'source': 'socket',
                    'type': 'IPv4'
                }
        except Exception:
            pass

        return {
            'ip': 'Не удалось определить',
            'source': 'none',
            'type': 'unknown'
        }

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Проверяет валидность IP-адреса"""
        # Проверка IPv4
        ipv4_pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if re.match(ipv4_pattern, ip):
            return True

        # Проверка IPv6 (упрощенная)
        if ':' in ip and len(ip) <= 45:
            return True

        return False

    @staticmethod
    def get_network_info() -> Dict:
        """
        Получает полную информацию о сети
        """
        return {
            'hostname': socket.gethostname(),
            'local_ip': IPAddressUtils.get_local_ip(),
            'all_ips': IPAddressUtils.get_all_local_ips(),
            'external_ip': IPAddressUtils.get_external_ip(),
            'system': platform.system(),
            'platform': platform.platform()
        }

    @staticmethod
    def get_ip_geolocation(ip: str, timeout: int = 5) -> Dict:
        """
        Получает геолокацию по IP-адресу

        Args:
            ip: IP-адрес для поиска
            timeout: Таймаут запроса

        Returns:
            Словарь с информацией о геолокации
        """
        if not IPAddressUtils._is_valid_ip(ip) or ip.startswith('127.') or ip.startswith('192.168.') or ip.startswith(
                '10.') or ip.startswith('172.'):
            return {
                'ip': ip,
                'country': 'Локальный IP',
                'city': 'Не доступно',
                'isp': 'Локальная сеть',
                'status': 'local'
            }

        services = [
            {
                'name': 'ipapi',
                'url': f'http://ip-api.com/json/{ip}',
                'parser': lambda data: {
                    'country': data.get('country', 'Неизвестно'),
                    'city': data.get('city', 'Неизвестно'),
                    'region': data.get('regionName', 'Неизвестно'),
                    'isp': data.get('isp', 'Неизвестно'),
                    'lat': data.get('lat'),
                    'lon': data.get('lon')
                }
            }
        ]

        for service in services:
            try:
                response = requests.get(service['url'], timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    result = service['parser'](data)
                    result.update({
                        'ip': ip,
                        'status': 'success',
                        'source': service['name']
                    })
                    return result
            except Exception as e:
                continue

        return {
            'ip': ip,
            'country': 'Не удалось определить',
            'city': 'Не доступно',
            'isp': 'Не доступно',
            'status': 'error'
        }

    @staticmethod
    def format_ip_info(info: Dict) -> str:
        """
        Форматирует информацию об IP в читаемую строку
        """
        lines = []

        if 'hostname' in info:
            lines.append(f"🐻 Имя хоста: {info['hostname']}")

        if 'local_ip' in info:
            lines.append(f"🏠 Основной локальный IP: {info['local_ip']}")

        if 'external_ip' in info and 'ip' in info['external_ip']:
            ext_ip = info['external_ip']
            lines.append(f"🌍 Внешний IP: {ext_ip['ip']} (источник: {ext_ip['source']})")

        if 'all_ips' in info:
            lines.append("\n📡 Сетевые интерфейсы:")
            for ip_info in info['all_ips']:
                line = f"  • {ip_info['interface']} ({ip_info['type']}):"
                if ip_info['ipv4']:
                    line += f" IPv4: {ip_info['ipv4']}"
                if ip_info['ipv6']:
                    line += f" IPv6: {ip_info['ipv6']}"
                lines.append(line)

        return '\n'.join(lines)


# Пример использования и тестирования
if __name__ == "__main__":
    print("=" * 50)
    print("УТИЛИТА ДЛЯ ПОЛУЧЕНИЯ IP-АДРЕСОВ")
    print("=" * 50)

    # Получаем полную информацию о сети
    network_info = IPAddressUtils.get_network_info()

    print(IPAddressUtils.format_ip_info(network_info))

    print("\n" + "=" * 50)
    print("ГЕОЛОКАЦИЯ ВНЕШНЕГО IP")
    print("=" * 50)

    # Получаем геолокацию внешнего IP
    if network_info['external_ip']['ip'] != 'Не удалось определить':
        geo_info = IPAddressUtils.get_ip_geolocation(network_info['external_ip']['ip'])
        if geo_info['status'] != 'local':
            print(f"IP: {geo_info['ip']}")
            print(f"Страна: {geo_info['country']}")
            print(f"Город: {geo_info['city']}")
            if 'region' in geo_info:
                print(f"Регион: {geo_info['region']}")
            print(f"Провайдер: {geo_info['isp']}")
        else:
            print("Внешний IP является локальным, геолокация недоступна")
    else:
        print("Не удалось получить внешний IP для геолокации")

    print("\n" + "=" * 50)
    print("БЫСТРЫЕ МЕТОДЫ")
    print("=" * 50)

    # Быстрые методы
    print(f"Основной локальный IP: {IPAddressUtils.get_local_ip()}")

    external_ip = IPAddressUtils.get_external_ip()
    print(f"Внешний IP: {external_ip['ip']}")

    print("\n" + "=" * 50)