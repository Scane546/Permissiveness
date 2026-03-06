import customtkinter as ctk
import subprocess
import psutil
import json
import os
import sys
from tkinter import messagebox
import native_dialog
import time
import threading
from PIL import Image

try:
    from pywinauto import Application
    from pywinauto.findwindows import ElementNotFoundError
    PYWINAUTO_AVAILABLE = True
except ImportError:
    PYWINAUTO_AVAILABLE = False

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

class VPNManager:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Permissiveness")
        self.root.geometry("800x600")
        
        # Установка иконки приложения
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
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
            except Exception as e:
                self.config = {
                    "portal_wg_path": "",
                    "portal_wg_config": "",
                    "zapret2_path": "",
                    "zapret_bat_folder": ""
                }
        else:
            self.config = {
                "portal_wg_path": "",
                "portal_wg_config": "",
                "zapret2_path": "",
                "zapret_bat_folder": ""
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
        try:
            logo_path = get_resource_path("logo.png")
            if os.path.exists(logo_path):
                # Открываем изображение и масштабируем пропорционально
                pil_image = Image.open(logo_path)
                # Масштабируем до ширины 600px с сохранением пропорций
                original_width = pil_image.width
                original_height = pil_image.height
                new_width = 600
                new_height = int((new_width / original_width) * original_height)
                
                logo_image = ctk.CTkImage(
                    light_image=pil_image,
                    dark_image=pil_image,
                    size=(new_width, new_height)
                )
                logo_label = ctk.CTkLabel(self.root, image=logo_image, text="")
                logo_label.pack(pady=10)
            else:
                # Если логотип не найден, показываем текст
                title = ctk.CTkLabel(self.root, text="Permissiveness", font=("Arial", 24, "bold"))
                title.pack(pady=30)
        except Exception as e:
            # Если ошибка загрузки, показываем текст
            title = ctk.CTkLabel(self.root, text="Permissiveness", font=("Arial", 24, "bold"))
            title.pack(pady=30)
        
        # РљРЅРѕРїРєР° 1: Portal WG
        btn1 = ctk.CTkButton(
            self.root, 
            text="Portal WG",
            command=self.launch_portal_wg,
            width=600,
            height=60,
            font=("Arial", 16)
        )
        btn1.pack(pady=10)
        
        # РљРЅРѕРїРєР° 2: Zapret 2
        btn2 = ctk.CTkButton(
            self.root,
            text="Zapret 2",
            command=self.launch_zapret2,
            width=600,
            height=60,
            font=("Arial", 16)
        )
        btn2.pack(pady=10)
        
        # Кнопка 3: Bat-файлы
        btn3 = ctk.CTkButton(
            self.root,
            text="Zapret.bat",
            command=self.show_bat_window,
            width=600,
            height=60,
            font=("Arial", 16)
        )
        btn3.pack(pady=10)
        
        # Кнопка 4: Завершить все процессы
        btn4 = ctk.CTkButton(
            self.root,
            text="Завершить процессы приложений обхода",
            command=self.kill_all_vpn,
            width=600,
            height=60,
            font=("Arial", 16),
            fg_color="red",
            hover_color="darkred"
        )
        btn4.pack(pady=10)
        
        # Кнопка 5: Настройки
        btn5 = ctk.CTkButton(
            self.root,
            text="Настройки путей",
            command=self.show_settings_window,
            width=600,
            height=60,
            font=("Arial", 16),
            fg_color="gray",
            hover_color="darkgray"
        )
        btn5.pack(pady=10)
    
    def launch_portal_wg(self):
        """Запуск Portal WG с автоматическим подключением"""
        if not self.config["portal_wg_path"]:
            return
        
        # Завершение всех VPN процессов
        killed = self.kill_vpn_processes()
        
        # Запуск Portal WG
        try:
            subprocess.Popen([self.config["portal_wg_path"]])
            
            # Запуск автоматического подключения в отдельном потоке
            threading.Thread(target=self.auto_connect_warp, daemon=True).start()
            
            # Уведомление только если процессы не были завершены
            if len(killed) == 0:
                messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        except:
            pass
    
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
    
    def launch_zapret2(self):
        """Запуск Zapret 2"""
        if not self.config["zapret2_path"]:
            return
        
        # Завершение всех VPN процессов
        killed = self.kill_vpn_processes()
        
        # Запуск Zapret 2
        try:
            subprocess.Popen([self.config["zapret2_path"]])
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
            subprocess.Popen([bat_path], cwd=self.config["zapret_bat_folder"], shell=True)
            # Уведомление только если процессы не были завершены
            if len(killed) == 0:
                messagebox.showinfo("Уведомление", "Ни один процесс не был завершен")
        except:
            pass
    
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
            command=self.show_main_window,
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



