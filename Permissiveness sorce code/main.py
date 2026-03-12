import customtkinter as ctk
import subprocess
import psutil
import json
import os
import sys
from tkinter import messagebox, Label, PhotoImage
import native_dialog
import time
import threading
from PIL import Image, ImageTk

try:
    from pywinauto import Application
    from pywinauto.findwindows import ElementNotFoundError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

try:
    import win32gui
    import win32con
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import pystray
    from pystray import MenuItem as item
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# Настройка темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_resource_path(relative_path):
    """Получить абсолютный путь к ресурсу (работает для .exe и .py)"""
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_image_path(image_name):
    """Получить путь к изображению из папки assets/images"""
    # Если запущен как exe
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        # Сначала ищем в папке assets/images рядом с exe
        image_path = os.path.join(exe_dir, "assets", "images", image_name)
        if os.path.exists(image_path):
            return image_path
        # Потом в упакованных ресурсах
        return get_resource_path(os.path.join("assets", "images", image_name))
    else:
        # Если запущен как скрипт
        image_path = os.path.join("assets", "images", image_name)
        if os.path.exists(image_path):
            return image_path
        # Fallback на старый путь для совместимости
        return image_name

class VPNManager:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Permissiveness")
        self.root.geometry("800x600")
        
        # Словарь для хранения иконок в трее и свернутых окон
        self.tray_icons = {}  # {app_name: {'icon': pystray_icon, 'windows': [hwnd1, hwnd2]}}
        
        # Установка иконки приложения
        try:
            icon_path = get_image_path("ico4.ico")
            if not os.path.exists(icon_path):
                icon_path = get_image_path("icon.ico")
            
            if icon_path and os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
                # Дополнительно устанавливаем иконку для панели задач
                try:
                    import io
                    img = Image.open(icon_path)
                    # Создаем PhotoImage для tkinter
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
                    self.root.iconphoto(True, photo._light_image)
                except:
                    pass
        except Exception as e:
            pass
        
        # Загрузка конфигурации - сохраняем рядом с exe
        if getattr(sys, 'frozen', False):
            # Если запущен как exe, сохраняем рядом с exe
            exe_dir = os.path.dirname(sys.executable)
            self.config_file = os.path.join(exe_dir, "config.json")
        else:
            # Если запущен как скрипт
            self.config_file = "config.json"
        
        self.load_config()
        
        # Загрузка списка процессов из файла
        # Ищем файл рядом с .exe или в рабочей директории
        if getattr(sys, 'frozen', False):
            # Если запущен как exe, ищем рядом с exe
            exe_dir = os.path.dirname(sys.executable)
            processes_file_exe = os.path.join(exe_dir, "processes_to_kill.txt")
            if os.path.exists(processes_file_exe):
                self.processes_file = processes_file_exe
            else:
                self.processes_file = get_resource_path("processes_to_kill.txt")
        else:
            # Если запущен как скрипт
            if os.path.exists("processes_to_kill.txt"):
                self.processes_file = "processes_to_kill.txt"
            else:
                self.processes_file = get_resource_path("processes_to_kill.txt")
        
        self.vpn_processes = self.load_processes_list()
        
        self.show_main_window()
    
    def load_processes_list(self):
        """Загрузка списка процессов из файла"""
        processes = []
        try:
            if os.path.exists(self.processes_file):
                with open(self.processes_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Игнорировать пустые строки и комментарии
                        if line and not line.startswith('#'):
                            processes.append(line)
            else:
                # Если файл не найден, создать с базовым списком
                self.create_default_processes_file()
                return self.load_processes_list()
        except:
            pass
        
        return processes
    
    def create_default_processes_file(self):
        """Создание файла со списком процессов по умолчанию"""
        default_content = """# Список процессов для завершения
# Каждый процесс на отдельной строке
# Строки начинающиеся с # игнорируются (комментарии)

# Zapret
Zapret
Zapret.exe
Zapret2
Zapret2.exe

# WinWS
winws2
winws2.exe
winws.exe
winws.exe (2)
winws.exe (3)
winws.exe (4)
winws.exe (5)

# WARP
Warp
WARP
WARP.exe

# Portal WG
PORTAL WG
PORTAL WG.exe
PortalWG
PortalWG.exe
"""
        # Создаем файл рядом с exe или в рабочей директории
        if getattr(sys, 'frozen', False):
            # Если запущен как exe, создаем рядом с exe
            exe_dir = os.path.dirname(sys.executable)
            file_path = os.path.join(exe_dir, "processes_to_kill.txt")
        else:
            file_path = "processes_to_kill.txt"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(default_content)
        self.processes_file = file_path
    
    def load_config(self):
        """Загрузка конфигурации из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # Добавляем новые поля если их нет
                if "enable_auto_connect" not in self.config:
                    # Миграция со старой настройки
                    if "disable_auto_connect" in self.config:
                        self.config["enable_auto_connect"] = not self.config["disable_auto_connect"]
                        del self.config["disable_auto_connect"]
                    else:
                        self.config["enable_auto_connect"] = True  # По умолчанию включено
                if "minimize_zapret2_to_tray" not in self.config:
                    self.config["minimize_zapret2_to_tray"] = False
                if "minimize_portal_wg_to_tray" not in self.config:
                    self.config["minimize_portal_wg_to_tray"] = False
                if "minimize_zapret_bat_to_tray" not in self.config:
                    self.config["minimize_zapret_bat_to_tray"] = False
            except Exception as e:
                self.config = {
                    "portal_wg_path": "",
                    "portal_wg_config": "",
                    "zapret2_path": "",
                    "zapret_bat_folder": "",
                    "enable_auto_connect": True,
                    "minimize_zapret2_to_tray": False,
                    "minimize_portal_wg_to_tray": False,
                    "minimize_zapret_bat_to_tray": False
                }
        else:
            self.config = {
                "portal_wg_path": "",
                "portal_wg_config": "",
                "zapret2_path": "",
                "zapret_bat_folder": "",
                "enable_auto_connect": True,
                "minimize_zapret2_to_tray": False,
                "minimize_portal_wg_to_tray": False,
                "minimize_zapret_bat_to_tray": False
            }
            self.save_config()
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    
    def kill_vpn_processes(self):
        """Завершение всех VPN процессов"""
        killed = []
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if proc_name in self.vpn_processes:
                    proc.kill()
                    killed.append(proc_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return killed
    
    def show_main_window(self):
        """Главное окно с 5 кнопками"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Логотип вместо текста
        logo_loaded = False
        try:
            logo_path = get_image_path("logo.png")
            
            if logo_path and os.path.exists(logo_path):
                # Открываем изображение и масштабируем пропорционально
                pil_image = Image.open(logo_path)
                # Масштабируем до ширины 600px с сохранением пропорций
                original_width = pil_image.width
                original_height = pil_image.height
                new_width = 600
                new_height = int((new_width / original_width) * original_height)
                
                self.logo_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height)
                )
                logo_label = ctk.CTkLabel(self.root, image=self.logo_image, text="")
                logo_label.pack(pady=10)
                logo_loaded = True
        except Exception as e:
            pass
        
        if not logo_loaded:
            # Если логотип не найден, показываем текст
            title = ctk.CTkLabel(self.root, text="Permissiveness", font=("Arial", 24, "bold"))
            title.pack(pady=30)
        
        # Кнопка 1: Portal WG с иконкой
        portal_wg_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        portal_wg_frame.pack(pady=10)
        
        # Кнопка на весь фрейм
        btn1 = ctk.CTkButton(
            portal_wg_frame, 
            text="Portal WG",
            command=self.launch_portal_wg,
            width=600,
            height=70,
            font=("Arial", 18)
        )
        btn1.pack()
        
        # Иконка поверх кнопки
        try:
            portal_wg_icon_path = get_image_path("Portal  WG ico.png")
            if os.path.exists(portal_wg_icon_path):
                portal_wg_pil = Image.open(portal_wg_icon_path)
                self.portal_wg_image = ctk.CTkImage(
                    light_image=portal_wg_pil,
                    dark_image=portal_wg_pil,
                    size=(60, 60)
                )
                
                # Получаем цвета кнопки
                button_color = btn1.cget("fg_color")
                hover_color = btn1.cget("hover_color")
                if isinstance(button_color, tuple):
                    button_color = button_color[1]
                if isinstance(hover_color, tuple):
                    hover_color = hover_color[1]
                
                portal_wg_icon_label = ctk.CTkLabel(portal_wg_frame, image=self.portal_wg_image, text="", fg_color=button_color)
                portal_wg_icon_label.place(x=10, y=5)
                
                # Обработчики для изменения цвета при наведении
                def on_enter_portal(e, label=portal_wg_icon_label, color=hover_color):
                    label.configure(fg_color=color)
                def on_leave_portal(e, label=portal_wg_icon_label, color=button_color):
                    label.configure(fg_color=color)
                
                btn1.bind("<Enter>", on_enter_portal)
                btn1.bind("<Leave>", on_leave_portal)
        except:
            pass
        
        # Кнопка 2: Zapret 2 с иконкой
        zapret2_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        zapret2_frame.pack(pady=10)
        
        # Кнопка на весь фрейм
        btn2 = ctk.CTkButton(
            zapret2_frame,
            text="Zapret 2",
            command=self.launch_zapret2,
            width=600,
            height=70,
            font=("Arial", 18)
        )
        btn2.pack()
        
        # Иконка поверх кнопки
        try:
            zapret2_icon_path = get_image_path("Zapret2.ico")
            if os.path.exists(zapret2_icon_path):
                zapret2_pil = Image.open(zapret2_icon_path)
                self.zapret2_image = ctk.CTkImage(
                    light_image=zapret2_pil,
                    dark_image=zapret2_pil,
                    size=(60, 60)
                )
                
                # Получаем цвета кнопки
                button_color = btn2.cget("fg_color")
                hover_color = btn2.cget("hover_color")
                if isinstance(button_color, tuple):
                    button_color = button_color[1]
                if isinstance(hover_color, tuple):
                    hover_color = hover_color[1]
                
                zapret2_icon_label = ctk.CTkLabel(zapret2_frame, image=self.zapret2_image, text="", fg_color=button_color)
                zapret2_icon_label.place(x=10, y=5)
                
                # Обработчики для изменения цвета при наведении
                def on_enter_zapret2(e, label=zapret2_icon_label, color=hover_color):
                    label.configure(fg_color=color)
                def on_leave_zapret2(e, label=zapret2_icon_label, color=button_color):
                    label.configure(fg_color=color)
                
                btn2.bind("<Enter>", on_enter_zapret2)
                btn2.bind("<Leave>", on_leave_zapret2)
        except:
            pass
        
        # Кнопка 3: Zapret.bat с иконкой
        zapret_bat_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        zapret_bat_frame.pack(pady=10)
        
        # Кнопка на весь фрейм
        btn3 = ctk.CTkButton(
            zapret_bat_frame,
            text="Zapret.bat",
            command=self.show_bat_window,
            width=600,
            height=70,
            font=("Arial", 18)
        )
        btn3.pack()
        
        # Иконка поверх кнопки
        try:
            zapret_bat_icon_path = get_image_path("Zapret.bat.png")
            if os.path.exists(zapret_bat_icon_path):
                zapret_bat_pil = Image.open(zapret_bat_icon_path)
                self.zapret_bat_image = ctk.CTkImage(
                    light_image=zapret_bat_pil,
                    dark_image=zapret_bat_pil,
                    size=(60, 60)
                )
                
                # Получаем цвета кнопки
                button_color = btn3.cget("fg_color")
                hover_color = btn3.cget("hover_color")
                if isinstance(button_color, tuple):
                    button_color = button_color[1]
                if isinstance(hover_color, tuple):
                    hover_color = hover_color[1]
                
                zapret_bat_icon_label = ctk.CTkLabel(zapret_bat_frame, image=self.zapret_bat_image, text="", fg_color=button_color)
                zapret_bat_icon_label.place(x=10, y=5)
                
                # Обработчики для изменения цвета при наведении
                def on_enter_bat(e, label=zapret_bat_icon_label, color=hover_color):
                    label.configure(fg_color=color)
                def on_leave_bat(e, label=zapret_bat_icon_label, color=button_color):
                    label.configure(fg_color=color)
                
                btn3.bind("<Enter>", on_enter_bat)
                btn3.bind("<Leave>", on_leave_bat)
        except:
            pass
        
        # Фрейм для кнопок на одной строке
        bottom_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bottom_frame.pack(pady=10)
        
        # Кнопка настройки (квадрат слева, выровнен под иконками)
        btn_settings = ctk.CTkButton(
            bottom_frame,
            text="⚙",
            command=self.show_settings_menu,
            width=80,
            height=70,
            font=("Arial", 50),
            fg_color="transparent",
            text_color="white",
            text_color_disabled="white",
            border_width=0
        )
        btn_settings.pack(side="left", padx=(0, 10))
        
        # Переменные для анимации
        self.settings_animation_running = False
        self.settings_animation_frames = ["⚙", "⚙", "⚙", "⚙"]  # Можно добавить разные символы для вращения
        self.settings_frame_index = 0
        
        # Обработчики для изменения цвета и анимации шестеренки при наведении
        def animate_settings():
            if self.settings_animation_running:
                self.settings_frame_index = (self.settings_frame_index + 1) % len(self.settings_animation_frames)
                btn_settings.configure(text=self.settings_animation_frames[self.settings_frame_index])
                self.root.after(100, animate_settings)  # Обновление каждые 100мс
        
        def on_enter_settings(e):
            btn_settings.configure(text_color="red")
            self.settings_animation_running = True
            animate_settings()
        
        def on_leave_settings(e):
            btn_settings.configure(text_color="white", text="⚙")
            self.settings_animation_running = False
            self.settings_frame_index = 0
        
        btn_settings.bind("<Enter>", on_enter_settings)
        btn_settings.bind("<Leave>", on_leave_settings)
        
        # Кнопка 4: Завершить все процессы (справа от настроек)
        btn4 = ctk.CTkButton(
            bottom_frame,
            text="Завершить процессы приложений обхода",
            command=self.kill_all_vpn,
            width=510,
            height=70,
            font=("Arial", 16),
            fg_color="red",
            hover_color="darkred"
        )
        btn4.pack(side="left")
    
    def launch_portal_wg(self):
        """Запуск Portal WG с автоматическим подключением"""
        if not self.config["portal_wg_path"]:
            return
        
        # Завершение всех VPN процессов
        killed = self.kill_vpn_processes()
        
        # Запуск Portal WG
        try:
            process = subprocess.Popen([self.config["portal_wg_path"]])
            
            # Если включено и автоподключение, и сворачивание - делаем последовательно
            auto_connect_enabled = self.config.get("enable_auto_connect", True)
            minimize_enabled = self.config.get("minimize_portal_wg_to_tray", False)
            
            if auto_connect_enabled and minimize_enabled:
                # Сначала автоподключение, потом сворачивание
                threading.Thread(target=self.auto_connect_and_minimize_portal_wg, args=(process.pid,), daemon=True).start()
            elif auto_connect_enabled:
                # Только автоподключение
                threading.Thread(target=self.auto_connect_warp, daemon=True).start()
            elif minimize_enabled:
                # Только сворачивание
                threading.Thread(target=self.minimize_to_tray, args=("PORTAL WG", process.pid), daemon=True).start()
            
            # Уведомление только если процессы не были завершены
            if len(killed) == 0:
                messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        except:
            pass
    
    def auto_connect_and_minimize_portal_wg(self, process_pid):
        """Автоподключение WARP, затем сворачивание в трей"""
        # Сначала автоподключение
        self.auto_connect_warp()
        # Ждем немного после подключения
        time.sleep(1)
        # Потом сворачивание
        self.minimize_to_tray("PORTAL WG", process_pid)
    
    def auto_connect_warp(self):
        """Автоматическое подключение WARP в Portal WG (без движения мыши)"""
        if not PYWINAUTO_AVAILABLE:
            return
        
        try:
            # Ждем загрузки приложения (сокращено до 2 секунд)
            time.sleep(0.5)
            
            # Подключаемся к окну Portal WG
            app = Application(backend="uia").connect(title_re=".*PORTAL WG.*", timeout=10)
            window = app.window(title_re=".*PORTAL WG.*")
            
            # Сначала выбираем конфиг, если указан
            if self.config.get("portal_wg_config"):
                try:
                    # Ищем элемент с названием конфига
                    config_name = self.config["portal_wg_config"]
                    config_item = window.child_window(title_re=f".*{config_name}.*")
                    if config_item.exists():
                        config_item.invoke()
                        time.sleep(0.3)  # Сокращено с 0.5
                except:
                    pass
            
            # Теперь ищем кнопку подключения
            button_texts = ["Подключить", "Connect", "Включить", "Enable"]
            
            for btn_text in button_texts:
                try:
                    button = window.child_window(title=btn_text, control_type="Button")
                    if button.exists():
                        button.invoke()  # Клик без движения мыши
                        return
                except:
                    continue
            
            # Если не нашли по тексту, пробуем найти все кнопки
            try:
                buttons = window.descendants(control_type="Button")
                if buttons:
                    # Кликаем на первую видимую активную кнопку
                    for btn in buttons:
                        if btn.is_visible() and btn.is_enabled():
                            btn.invoke()
                            break
            except:
                pass
                
        except:
            # Не выводим ошибки - они не критичны
            pass
    
    def minimize_to_tray(self, window_title_part, process_pid, minimize_all=False):
        """Сворачивание окна в трей с созданием иконки
        
        Args:
            window_title_part: Часть заголовка окна для поиска
            process_pid: PID процесса (не используется, оставлен для совместимости)
            minimize_all: Если True, сворачивает все найденные окна (для Zapret 2)
        """
        if not WIN32_AVAILABLE:
            return
        
        try:
            # Ждем появления окна
            time.sleep(2)
            
            # Ищем окно по части заголовка
            def find_window_by_title(title_part):
                windows = []
                def callback(hwnd, extra):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        if title_part.lower() in window_text.lower():
                            windows.append(hwnd)
                    return True
                
                win32gui.EnumWindows(callback, None)
                return windows
            
            # Пытаемся найти окно несколько раз
            max_attempts = 15 if minimize_all else 10
            found_windows = []
            
            for attempt in range(max_attempts):
                windows = find_window_by_title(window_title_part)
                if windows:
                    for hwnd in windows:
                        if hwnd not in found_windows:
                            found_windows.append(hwnd)
                            # Сворачиваем окно
                            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                            # Скрываем с панели задач
                            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    
                    # Если minimize_all, продолжаем искать новые окна
                    if minimize_all:
                        time.sleep(1)
                        continue
                    else:
                        break
                time.sleep(1)
            
            # Создаем иконку в трее если нашли окна
            if found_windows and PYSTRAY_AVAILABLE:
                self.create_tray_icon(window_title_part, found_windows)
                
        except Exception as e:
            pass
    
    def create_tray_icon(self, app_name, window_handles):
        """Создание иконки в системном трее"""
        if not PYSTRAY_AVAILABLE:
            return
        
        try:
            # Определяем иконку в зависимости от приложения
            icon_file = "ico4.ico"  # По умолчанию
            if "zapret" in app_name.lower():
                if "winws" in app_name.lower():
                    icon_file = "Zapret.bat.png"
                else:
                    icon_file = "Zapret2.ico"
            elif "portal" in app_name.lower():
                icon_file = "Portal  WG ico.png"
            
            icon_path = get_image_path(icon_file)
            if not os.path.exists(icon_path):
                icon_path = get_image_path("ico4.ico")
            
            # Загружаем иконку
            image = Image.open(icon_path)
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Создаем меню для иконки
            menu = pystray.Menu(
                item('Развернуть', lambda: self.restore_windows(app_name)),
                item('Закрыть иконку', lambda: self.remove_tray_icon(app_name))
            )
            
            # Создаем иконку
            icon = pystray.Icon(
                f"permissiveness_{app_name}",
                image,
                app_name,
                menu
            )
            
            # Сохраняем информацию
            self.tray_icons[app_name] = {
                'icon': icon,
                'windows': window_handles
            }
            
            # Запускаем иконку в отдельном потоке
            threading.Thread(target=icon.run, daemon=True).start()
            
            # Запускаем мониторинг окон
            threading.Thread(target=self.monitor_windows, args=(app_name,), daemon=True).start()
            
        except Exception as e:
            pass
    
    def monitor_windows(self, app_name):
        """Мониторинг окон - автоматически удаляет иконку если все окна закрыты"""
        if app_name not in self.tray_icons:
            return
        
        try:
            while app_name in self.tray_icons:
                time.sleep(2)  # Проверяем каждые 2 секунды
                
                windows = self.tray_icons[app_name]['windows']
                all_closed = True
                
                # Проверяем каждое окно
                for hwnd in windows:
                    try:
                        if win32gui.IsWindow(hwnd):
                            all_closed = False
                            break
                    except:
                        pass
                
                # Если все окна закрыты - удаляем иконку
                if all_closed:
                    self.remove_tray_icon(app_name)
                    break
                    
        except Exception as e:
            pass
    
    def restore_windows(self, app_name):
        """Разворачивание окон из трея"""
        if app_name not in self.tray_icons:
            return
        
        try:
            windows = self.tray_icons[app_name]['windows']
            for hwnd in windows:
                try:
                    # Показываем окно
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    # Разворачиваем
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    # Выводим на передний план
                    win32gui.SetForegroundWindow(hwnd)
                except:
                    pass
            
            # Удаляем иконку из трея
            self.remove_tray_icon(app_name)
            
        except Exception as e:
            pass
    
    def remove_tray_icon(self, app_name):
        """Удаление иконки из трея"""
        if app_name in self.tray_icons:
            try:
                icon = self.tray_icons[app_name]['icon']
                icon.stop()
                del self.tray_icons[app_name]
            except:
                pass
    
    def launch_zapret2(self):
        """Запуск Zapret 2"""
        if not self.config["zapret2_path"]:
            return
        
        # Завершение всех VPN процессов
        killed = self.kill_vpn_processes()
        
        # Запуск Zapret 2
        try:
            process = subprocess.Popen([self.config["zapret2_path"]])
            
            # Сворачивание в трей если включено (сворачиваем все окна - загрузочное и основное)
            if self.config.get("minimize_zapret2_to_tray", False):
                threading.Thread(target=self.minimize_to_tray, args=("Zapret", process.pid, True), daemon=True).start()
            
            # Уведомление только если процессы не были завершены
            if len(killed) == 0:
                messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        except:
            pass
    
    def kill_all_vpn(self):
        """Завершение всех VPN процессов"""
        killed = self.kill_vpn_processes()
        if len(killed) == 0:
            messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        # Если процессы были завершены - ничего не показываем

    
    def show_bat_window(self):
        """Окно с bat-файлами"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Выберите Bat-файл", font=("Arial", 24, "bold"))
        title.pack(pady=20)
        
        # Создание прокручиваемого фрейма
        scroll_frame = ctk.CTkScrollableFrame(self.root, width=700, height=450)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Список bat-файлов
        bat_files = [
            "general (ALT).bat",
            "general (ALT2).bat",
            "general (ALT3).bat",
            "general (ALT4).bat",
            "general (ALT5).bat",
            "general (ALT6).bat",
            "general (ALT7).bat",
            "general (ALT8).bat",
            "general (ALT9).bat",
            "general (ALT10).bat",
            "general (ALT11).bat",
            "general (FAKE TLS AUTO ALT).bat",
            "general (FAKE TLS AUTO ALT2).bat",
            "general (FAKE TLS AUTO ALT3).bat",
            "general (FAKE TLS AUTO).bat",
            "general (SIMPLE FAKE ALT).bat",
            "general (SIMPLE FAKE ALT2).bat",
            "general (SIMPLE FAKE).bat"
        ]
        
        # Создание кнопок для каждого bat-файла
        for bat_file in bat_files:
            btn = ctk.CTkButton(
                scroll_frame,
                text=bat_file,
                command=lambda f=bat_file: self.launch_bat_file(f),
                width=650,
                height=50,
                font=("Arial", 14)
            )
            btn.pack(pady=5)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_main_window,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=10)
    
    def launch_bat_file(self, bat_file):
        """Запуск выбранного bat-файла"""
        if not self.config["zapret_bat_folder"]:
            return
        
        bat_path = os.path.join(self.config["zapret_bat_folder"], bat_file)
        
        if not os.path.exists(bat_path):
            return
        
        # Завершение всех VPN процессов
        killed = self.kill_vpn_processes()
        
        # Запуск bat-файла
        try:
            process = subprocess.Popen([bat_path], cwd=self.config["zapret_bat_folder"], shell=True)
            
            # Сворачивание в трей если включено
            if self.config.get("minimize_zapret_bat_to_tray", False):
                # Ищем окна с разными вариантами названий
                # winws, cmd, консольные окна с zapret
                threading.Thread(target=self.minimize_bat_windows, args=(process.pid,), daemon=True).start()
            
            # Уведомление только если процессы не были завершены
            if len(killed) == 0:
                messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        except:
            pass
    
    def minimize_bat_windows(self, process_pid):
        """Специальная функция для сворачивания окон Zapret.bat"""
        if not WIN32_AVAILABLE:
            return
        
        try:
            # Ждем запуска процессов
            time.sleep(3)
            
            # Ищем окна по разным критериям
            def find_bat_windows():
                windows = []
                def callback(hwnd, extra):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd).lower()
                        # Ищем окна с winws, cmd, или консольные окна
                        if any(keyword in window_text for keyword in ['winws', 'zapret', 'cmd', 'консоль']):
                            windows.append(hwnd)
                    return True
                
                win32gui.EnumWindows(callback, None)
                return windows
            
            # Пытаемся найти окна несколько раз
            found_windows = []
            for attempt in range(20):  # Больше попыток для bat файлов
                windows = find_bat_windows()
                for hwnd in windows:
                    if hwnd not in found_windows:
                        found_windows.append(hwnd)
                        # Сворачиваем окно
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                        # Скрываем с панели задач
                        win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                
                time.sleep(1)
            
            # Создаем иконку в трее если нашли окна
            if found_windows and PYSTRAY_AVAILABLE:
                self.create_tray_icon("Zapret.bat (winws)", found_windows)
                
        except Exception as e:
            pass
    
    def show_settings_menu(self):
        """Главное меню настроек"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Настройки", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # Кнопка: Настройка путей
        btn_paths = ctk.CTkButton(
            self.root,
            text="Настройка путей",
            command=self.show_settings_window,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_paths.pack(pady=15)
        
        # Кнопка: Общие настройки
        btn_general = ctk.CTkButton(
            self.root,
            text="Общие настройки",
            command=self.show_general_settings,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_general.pack(pady=15)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_main_window,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=30)
    
    def show_general_settings(self):
        """Окно общих настроек с галочками"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Общие настройки", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # Фрейм для галочек
        checkboxes_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        checkboxes_frame.pack(pady=20)
        
        # Галочка 1: Включить автоподключение WARP
        self.enable_auto_connect_var = ctk.BooleanVar(value=self.config.get("enable_auto_connect", True))
        checkbox1 = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Включить автоподключение WARP",
            variable=self.enable_auto_connect_var,
            font=("Arial", 16),
            checkbox_width=30,
            checkbox_height=30
        )
        checkbox1.pack(pady=15, anchor="w", padx=50)
        
        # Галочка 2: Сворачивать Zapret 2 в трей
        self.minimize_zapret2_var = ctk.BooleanVar(value=self.config.get("minimize_zapret2_to_tray", False))
        checkbox2 = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Сворачивать Zapret 2 в трей",
            variable=self.minimize_zapret2_var,
            font=("Arial", 16),
            checkbox_width=30,
            checkbox_height=30
        )
        checkbox2.pack(pady=15, anchor="w", padx=50)
        
        # Галочка 3: Сворачивать Portal WG в трей
        self.minimize_portal_wg_var = ctk.BooleanVar(value=self.config.get("minimize_portal_wg_to_tray", False))
        checkbox3 = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Сворачивать Portal WG в трей",
            variable=self.minimize_portal_wg_var,
            font=("Arial", 16),
            checkbox_width=30,
            checkbox_height=30
        )
        checkbox3.pack(pady=15, anchor="w", padx=50)
        
        # Галочка 4: Сворачивать Zapret.bat в трей
        self.minimize_zapret_bat_var = ctk.BooleanVar(value=self.config.get("minimize_zapret_bat_to_tray", False))
        checkbox4 = ctk.CTkCheckBox(
            checkboxes_frame,
            text="Сворачивать Zapret.bat в трей",
            variable=self.minimize_zapret_bat_var,
            font=("Arial", 16),
            checkbox_width=30,
            checkbox_height=30
        )
        checkbox4.pack(pady=15, anchor="w", padx=50)
        
        # Кнопка сохранить
        save_btn = ctk.CTkButton(
            self.root,
            text="Сохранить",
            command=self.save_general_settings,
            width=300,
            height=50,
            font=("Arial", 16),
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(pady=30)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_settings_menu,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=10)
    
    def save_general_settings(self):
        """Сохранение общих настроек"""
        self.config["enable_auto_connect"] = self.enable_auto_connect_var.get()
        self.config["minimize_zapret2_to_tray"] = self.minimize_zapret2_var.get()
        self.config["minimize_portal_wg_to_tray"] = self.minimize_portal_wg_var.get()
        self.config["minimize_zapret_bat_to_tray"] = self.minimize_zapret_bat_var.get()
        self.save_config()
        messagebox.showinfo("Успешно", "Настройки сохранены")
    
    def show_settings_window(self):
        """Окно настроек"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Задать расположение:", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # РљРЅРѕРїРєР° Portal WG
        btn_portal = ctk.CTkButton(
            self.root,
            text="Portal WG",
            command=self.show_portal_wg_settings,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_portal.pack(pady=15)
        
        # РљРЅРѕРїРєР° Zapret 2
        btn_zapret2 = ctk.CTkButton(
            self.root,
            text="Zapret 2",
            command=self.show_zapret2_settings,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_zapret2.pack(pady=15)
        
        # РљРЅРѕРїРєР° Zapret.bat
        btn_bat = ctk.CTkButton(
            self.root,
            text="Zapret.bat",
            command=self.show_bat_settings,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_bat.pack(pady=15)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_settings_menu,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=30)

    
    def show_portal_wg_settings(self):
        """Настройки Portal WG"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Настройки Portal WG", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # РљРЅРѕРїРєР° РѕР±Р·РѕСЂ
        btn_browse = ctk.CTkButton(
            self.root,
            text="Обзор (выбрать .exe файл)",
            command=self.browse_portal_wg,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_browse.pack(pady=15)
        
        # Текущий путь
        current_path = ctk.CTkLabel(
            self.root,
            text=f"Текущий путь: {self.config['portal_wg_path'] or 'Не задан'}",
            font=("Arial", 12),
            wraplength=700
        )
        current_path.pack(pady=10)
        
        # Поле для имени конфига
        config_label = ctk.CTkLabel(self.root, text="Имя конфига:", font=("Arial", 16))
        config_label.pack(pady=(30, 5))
        
        self.portal_config_entry = ctk.CTkEntry(
            self.root,
            width=600,
            height=50,
            font=("Arial", 14),
            placeholder_text="Например: STR.WARP38605"
        )
        self.portal_config_entry.pack(pady=10)
        
        # Вставка текущего значения без привязки к языку
        if self.config["portal_wg_config"]:
            self.portal_config_entry.delete(0, 'end')
            self.portal_config_entry.insert(0, self.config["portal_wg_config"])
        
        # Кнопка сохранить
        save_btn = ctk.CTkButton(
            self.root,
            text="Сохранить",
            command=self.save_portal_wg_config,
            width=300,
            height=50,
            font=("Arial", 16),
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(pady=20)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_settings_window,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=10)
    
    def browse_portal_wg(self):
        """Выбор файла Portal WG"""
        file_path = native_dialog.askopenfilename(
            title="Выберите Portal WG.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.config["portal_wg_path"] = file_path
            self.save_config()
            self.show_portal_wg_settings()  # Обновить окно
    
    def save_portal_wg_config(self):
        """Сохранение имени конфига Portal WG"""
        self.config["portal_wg_config"] = self.portal_config_entry.get()
        self.save_config()
        # Убрано уведомление
    
    def show_zapret2_settings(self):
        """Настройки Zapret 2"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Настройки Zapret 2", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # РљРЅРѕРїРєР° РѕР±Р·РѕСЂ
        btn_browse = ctk.CTkButton(
            self.root,
            text="Обзор (выбрать .exe файл)",
            command=self.browse_zapret2,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_browse.pack(pady=15)
        
        # Текущий путь
        current_path = ctk.CTkLabel(
            self.root,
            text=f"Текущий путь: {self.config['zapret2_path'] or 'Не задан'}",
            font=("Arial", 12),
            wraplength=700
        )
        current_path.pack(pady=10)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_settings_window,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=30)
    
    def browse_zapret2(self):
        """Выбор файла Zapret 2"""
        file_path = native_dialog.askopenfilename(
            title="Выберите Zapret.exe",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.config["zapret2_path"] = file_path
            self.save_config()
            self.show_zapret2_settings()  # Обновить окно
    
    def show_bat_settings(self):
        """Настройки Zapret.bat"""
        # Очистка окна
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Заголовок
        title = ctk.CTkLabel(self.root, text="Настройки Zapret.bat", font=("Arial", 24, "bold"))
        title.pack(pady=30)
        
        # РљРЅРѕРїРєР° РѕР±Р·РѕСЂ
        btn_browse = ctk.CTkButton(
            self.root,
            text="Обзор (выбрать папку)",
            command=self.browse_bat_folder,
            width=600,
            height=70,
            font=("Arial", 16)
        )
        btn_browse.pack(pady=15)
        
        # Текущий путь
        current_path = ctk.CTkLabel(
            self.root,
            text=f"Текущая папка: {self.config['zapret_bat_folder'] or 'Не задана'}",
            font=("Arial", 12),
            wraplength=700
        )
        current_path.pack(pady=10)
        
        # Кнопка назад
        back_btn = ctk.CTkButton(
            self.root,
            text="Назад",
            command=self.show_settings_window,
            width=200,
            height=40,
            fg_color="gray",
            hover_color="darkgray"
        )
        back_btn.pack(pady=30)
    
    def browse_bat_folder(self):
        """Выбор папки с bat-файлами"""
        folder_path = native_dialog.askdirectory(
            title="Выберите папку с bat-файлами",
            parent=self.root
        )
        if folder_path:
            self.config["zapret_bat_folder"] = folder_path
            self.save_config()
            self.show_bat_settings()  # Обновить окно
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


if __name__ == "__main__":
    app = VPNManager()
    app.run()



