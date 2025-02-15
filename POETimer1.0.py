import customtkinter as ctk
import tkinter as tk
import time
import keyboard
import threading
import json
import os
from tkinter import filedialog


class POESpeedrunTimer:

    def monitor_poe_log(self):
        """Отслеживает смену локаций в Client.txt и вызывает split_time()."""
        
        log_path = os.path.join(self.log_path, "Client.txt")  # Используем self.log_path
        print(f"Monitoring log file at: {log_path}")  # Проверяем путь перед запуском
        
        if not os.path.exists(log_path):
            print("Log file not found!")
            return

        with open(log_path, "r", encoding="utf-8") as f:
            f.seek(0, os.SEEK_END)  # Начинаем с конца файла

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)  # Проверяем каждые 500 мс
                    continue

                if "You have entered" in line:
                    location = line.split("You have entered")[-1].strip().replace(".", "")

                    if self.splits and self.splits[-1] == location:
                        continue  # Если последняя локация та же, что и новая, ничего не делаем

                    if location not in self.splits:
                        self.splits.append(location)  # Добавляем новую локацию
                        self.best_times.setdefault(location, None)  # Убедимся, что ключ есть в best_times
                        print(f"Добавлена новая локация: {location}")

                    if location in self.splits:
                        print(f"Переключение сплита: {location}")
                        self.split_time()






    def __init__(self, root):
        print("Программа запущена!")
        print("ПОЕ ТАЙМЕР: Создание экземпляра класса...")


        self.root = root
        self.root.title("PoE Speedrun Timer")
        self.root.geometry("350x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#222")
        self.hotkeys = {
            "start": "F5",
            "split": "F6",
            "reset": "F8"
        }

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.start_time = 0
        self.elapsed_time = 0
        self.running = False
        self.always_on_top = True
        self.timer_color = "red"
        self.settings_window = None
        self.log_path = ""  # Или какой-то стандартный путь по умолчанию

        self.splits = self.load_splits()
        self.current_split = 0
        self.best_times = {split: None for split in self.splits}

        self.root.attributes('-topmost', self.always_on_top)

        # Основной таймер
        self.label = ctk.CTkLabel(root, text="00:00.000", font=("Arial", 32, "bold"), text_color=self.timer_color)
        self.label.pack(pady=10)

        self.create_buttons()
        self.create_split_section()
        self.update_splits_ui()

        self.update_timer()
        threading.Thread(target=self.listen_keys, daemon=True).start()
        threading.Thread(target=self.monitor_poe_log, daemon=True).start()


    def create_buttons(self):
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=5)

        self.start_button = ctk.CTkButton(button_frame, text="▶ Start (F5)",
                                        command=self.start_timer,
                                        corner_radius=20, width=80, height=35,
                                        fg_color="#444", font=("Arial", 14))
        self.start_button.grid(row=0, column=0, padx=2, pady=2, sticky="nsew")

        self.save_button = ctk.CTkButton(button_frame, text="💾 Save",
                                 command=self.save_splits_history,
                                 corner_radius=20, width=80, height=35,
                                 fg_color="#555", font=("Arial", 12))
        self.save_button.grid(row=1, column=0, padx=2, pady=2, sticky="nsew")


        self.reset_button = ctk.CTkButton(button_frame, text="Reset (F8)",
                                        command=self.reset_timer,
                                        corner_radius=20, width=80, height=35,
                                        fg_color="#444", font=("Arial", 14))
        self.reset_button.grid(row=0, column=1, padx=2, pady=2, sticky="nsew")

        self.settings_button = ctk.CTkButton(button_frame, text="⚙ Settings", command=self.open_settings, corner_radius=15, width=80)
        self.settings_button.grid(row=1, column=1, padx=2, pady=2)


    def save_splits_history(self):
        """Сохраняет историю сплитов в файл splits_history.json"""
        data = {"splits": self.splits, "times": self.best_times}
        with open("splits_history.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("Сохранено в splits_history.json")


        

    def update_timer(self):
        if self.running:
            self.elapsed_time = time.time() - self.start_time
        self.label.configure(text=self.format_time(self.elapsed_time), text_color=self.timer_color)
        self.root.after(50, self.update_timer)

    def start_timer(self):
        self.running = not self.running
        if self.running:
            self.start_time = time.time() - self.elapsed_time
            self.start_button.configure(text="⏹ Stop (F5)")
        else:
            self.start_button.configure(text="▶ Start (F5)")

    def split_time(self):
        if self.running and self.current_split < len(self.splits):
            formatted_time = self.format_time(self.elapsed_time)
            split_name = self.splits[self.current_split]

            # Сохранение лучшего времени
            if self.best_times[split_name] is None or self.elapsed_time < self.best_times[split_name]:
                self.best_times[split_name] = self.elapsed_time  

            self.current_split += 1
            self.update_splits_ui()
            self.save_splits()

    def save_splits(self):
        """Сохраняет текущие сплиты в файл splits.json."""
        with open("splits.json", "w") as file:
            json.dump(self.splits, file, indent=4)

    def reset_timer(self):
        self.running = False
        self.elapsed_time = 0
        self.current_split = 0
        self.label.configure(text="00:00.000")
        self.start_button.configure(text="▶ Start (F5)")
        self.best_times = {split: None for split in self.splits}
        self.splits = []
        self.best_times = {}
        self.update_splits_ui()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.root.attributes('-topmost', self.always_on_top)
        self.pin_button.configure(text="✅ Locked" if self.always_on_top else "❌ Unlocked")


    def listen_keys(self):
        keyboard.add_hotkey(self.hotkeys["start"], self.start_timer)
        #keyboard.add_hotkey(self.hotkeys["split"], self.split_time)
        keyboard.add_hotkey(self.hotkeys["reset"], self.reset_timer)
        keyboard.wait()


    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Настройки")
        self.settings_window.geometry("330x500")
        ctk.CTkLabel(self.settings_window, text="Path to PoE Logs:", text_color="white").pack(pady=5)

        # self.log_path_entry = ctk.CTkEntry(self.settings_window, width=300)  # Поле для ввода пути
        # self.log_path_entry.insert(0, self.log_path)  # Устанавливаем текущий путь
        # self.log_path_entry.pack(pady=5)

        self.save_path_button = ctk.CTkButton(self.settings_window, text="Save Path", command=self.save_log_path, corner_radius=15)
        self.save_path_button.pack(pady=5)


        x, y = self.root.winfo_x() + self.root.winfo_width() + 10, self.root.winfo_y()
        self.settings_window.geometry(f"+{x}+{y}")
        self.settings_window.configure(bg="#333")

        ctk.CTkLabel(self.settings_window, text="Настройка горячих клавиш:", text_color="white").pack(pady=10)

        self.entry_widgets = {}

        for key in self.hotkeys:
            frame = ctk.CTkFrame(self.settings_window)
            frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(frame, text=key, width=80).pack(side="left", padx=5)

            button = ctk.CTkButton(frame, text=self.hotkeys[key], width=100,
                        command=lambda k=key: self.bind_key(k))
            button.pack(side="left", padx=5)
            self.entry_widgets[key] = button  

        # Кнопка Apply
        ctk.CTkButton(self.settings_window, text="Apply", 
                    command=self.update_hotkeys, corner_radius=15).pack(pady=10)

        #
                        # Ползунок прозрачности
        ctk.CTkLabel(self.settings_window, text="Прозрачность:", text_color="white").pack(pady=5)
        
        self.opacity_slider = ctk.CTkSlider(self.settings_window, from_=0.1, to=1.0, number_of_steps=25,
                                            command=self.set_opacity)
        self.opacity_slider.set(self.root.attributes("-alpha"))  # Устанавливаем текущее значение
        self.opacity_slider.pack(pady=5)

        # Раздел для изменения пути к логам
        ctk.CTkLabel(self.settings_window, text="Path to PoE Logs:", text_color="white").pack(pady=5)

        self.log_path_entry = ctk.CTkEntry(self.settings_window, width=300)
        self.log_path_entry.insert(0, self.log_path)  # Текущий путь
        self.log_path_entry.pack(pady=5)

        browse_button = ctk.CTkButton(self.settings_window, text="Browse", command=self.browse_log_path)
        browse_button.pack(pady=5)


        ctk.CTkButton(self.settings_window, text="Save Path", command=self.save_log_path, corner_radius=15).pack(pady=5)

    def save_log_path(self):
        """Сохраняет новый путь к логам и перезапускает мониторинг"""
        new_path = self.log_path_entry.get().strip()

        if os.path.exists(new_path):
            self.log_path = new_path  # Обновляем путь в переменной
            print(f"Log path updated: {self.log_path}")  # Проверяем, обновился ли путь

            # Останавливаем текущий поток (если есть)
            if hasattr(self, "log_thread") and self.log_thread.is_alive():
                self.stop_monitoring = True  # Флаг для остановки потока
                self.log_thread.join()  # Ждём завершения

            # Сбрасываем флаг и перезапускаем мониторинг логов
            self.stop_monitoring = False
            self.log_thread = threading.Thread(target=self.monitor_poe_log, daemon=True)
            self.log_thread.start()
        else:
            print("Invalid path. Please enter a valid path.")


    def browse_log_path(self):
        """Открывает проводник для выбора папки с логами"""
        print("Opening folder selection dialog...")  # Отладочный вывод
        self.root.withdraw()  # Скрываем основное окно временно
        folder_selected = filedialog.askdirectory(title="Select Path of Exile Logs Folder")
        self.root.deiconify()  # Возвращаем главное окно после выбора

        if folder_selected:
            self.log_path_entry.delete(0, "end")  # Очищаем поле ввода
            self.log_path_entry.insert(0, folder_selected)  # Вставляем новый путь
            print(f"Selected log path: {folder_selected}")  # Выводим в терминал




    

    def set_opacity(self, value):
        """Меняет прозрачность окна"""
        self.root.attributes("-alpha", float(value))



            


    hotkey_entries = {}

    def reset_to_defaults(self):
        """Сбрасывает горячие клавиши на значения по умолчанию."""
        self.hotkeys = {"start": "F5", "split": "F6", "reset": "F8"}

        for key, button in self.entry_widgets.items():
            button.configure(text=self.hotkeys[key])  # <-- Правильное обновление кнопок


        ctk.CTkButton(self.settings_window, text="Defaults",
              command=self.reset_to_defaults, corner_radius=15).pack(pady=10)
    
    


    def create_split_section(self):
        ctk.CTkFrame(self.root, height=2, fg_color="#777").pack(fill="x", pady=5)
        split_frame = ctk.CTkFrame(self.root, fg_color="#1e1e1e", corner_radius=10)
        split_frame.pack(pady=5, fill="both", expand=True)

        self.split_location_box = ctk.CTkFrame(split_frame, fg_color="#1e1e1e")
        self.split_location_box.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.split_time_box = ctk.CTkFrame(split_frame, fg_color="#1e1e1e")
        self.split_time_box.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Добавляем списки для хранения Label элементов
        self.split_location_labels = []
        self.split_time_labels = []

        for split in self.splits:
            label_loc = ctk.CTkLabel(self.split_location_box, text=split, font=("Arial", 14), text_color="white")
            label_loc.pack(anchor="w", padx=5)
            self.split_location_labels.append(label_loc)

            label_time = ctk.CTkLabel(self.split_time_box, text="--:--.---", font=("Arial", 14, "bold"), text_color="white")
            label_time.pack(anchor="e", padx=5)
            self.split_time_labels.append(label_time)



        split_frame.columnconfigure(0, weight=1)
        split_frame.columnconfigure(1, weight=1)

    def load_splits(self):
        """Очищает список сплитов при запуске, но оставляет файл."""
        self.splits = []  # Очищаем список, но не удаляем файл
        return self.splits

    def add_location(self, location_name):
        """Добавляет новую локацию и обновляет UI."""
        if location_name not in self.splits:
            self.splits.append(location_name)
            self.best_times[location_name] = None  # Исправление ошибки KeyError
            self.best_times.setdefault(location_name, None)
            self.save_splits()  # Сохраняем изменения
            print(f"Добавлена новая локация: {location_name}")
            self.update_splits_ui()
            


    
    def reset_splits(self):
        """Перезаписывает splits.json с новыми значениями."""
        self.splits = self.load_splits()  # Загружаем сохранённые сплиты (или пустой список)
        self.save_splits()
        self.update_splits_ui()


    def update_splits_ui(self):
        """Обновляет список сплитов и их таймеров."""
        
        # Удаляем все существующие виджеты перед обновлением
        for widget in self.split_location_box.winfo_children():
            widget.destroy()
        for widget in self.split_time_box.winfo_children():
            widget.destroy()

        # Очищаем старые списки
        self.split_location_labels.clear()
        self.split_time_labels.clear()

        print(self.splits)  # Проверяем, что список обновляется

        # Создаём новые метки для каждой локации и таймера
        for i, split in enumerate(self.splits):
            best_time = self.best_times.get(split, None)
            best_time_str = self.format_time(best_time) if best_time else "--:--.---"

            label_color = "yellow" if i == self.current_split else "white"
            label_weight = "bold" if i == self.current_split else "normal"

            # Локация (название)
            label_loc = ctk.CTkLabel(self.split_location_box, text=split, font=("Arial", 14), text_color=label_color)
            label_loc.pack(anchor="w", padx=5)
            self.split_location_labels.append(label_loc)

            # Время сплита (таймер)
            label_time = ctk.CTkLabel(self.split_time_box, text=best_time_str, font=("Arial", 14, label_weight), text_color="white")
            label_time.pack(anchor="e", padx=5)
            self.split_time_labels.append(label_time)




    def format_time(self, seconds):
                """Форматирует время в формат MM:SS.mmm"""
                if seconds is None:
                    return "--:--.---"
                minutes, sec = divmod(int(seconds), 60)
                millis = int((seconds % 1) * 1000)
                return f"{minutes:02}:{sec:02}.{millis:03}"
    
    def save_splits(self):
        """Сохраняет сплиты в файл splits.json."""
        with open("splits.json", "w") as file:
            json.dump(self.splits, file)


    def bind_key(self, key):
        """Ожидает нажатия клавиши и меняет горячую клавишу."""
        self.entry_widgets[key].configure(text="Press a key...")

        def on_key_event(event):
            key_name = event.name.upper() if hasattr(event, "name") else str(event).upper()
            self.hotkeys[key] = key_name
            self.entry_widgets[key].configure(text=key_name)
            keyboard.unhook_all()  # Удаляем привязки после выбора клавиши

        keyboard.on_press(on_key_event)  # Ждём ввод одной клавиши


    def update_hotkeys(self):
            """Применяет новые горячие клавиши"""
            for key, entry in self.entry_widgets.items():
                new_key = entry.cget("text").upper()
                if new_key and new_key != "BIND A KEY":
                    self.hotkeys[key] = new_key  # Обновляем привязку клавиши

            self.settings_window.destroy()  # Закрываем окно после сохранения

            # Удаляем старые привязки
            keyboard.unhook_all()

            # Перепривязываем горячие клавиши
            keyboard.add_hotkey(self.hotkeys["start"], self.start_timer)
            keyboard.add_hotkey(self.hotkeys["split"], self.split_time)
            keyboard.add_hotkey(self.hotkeys["reset"], self.reset_timer)
            


            for key, label in [("start", "Старт:"), ("split", "Сплит:"), ("reset", "Сброс:")]:
                frame = ctk.CTkFrame(self.settings_window)
                frame.pack(pady=2, fill="x", padx=10)

                ctk.CTkLabel(frame, text=label, text_color="white").pack(side="left", padx=5)
                entry = ctk.CTkEntry(frame, width=100)  # Увеличиваем ширину
                entry.insert(0, "Bind a key")  # Добавляем placeholder
                entry.bind("<FocusIn>", lambda event, e=entry: e.delete(0, "end") if e.get() == "Bind a key" else None)  
                entry.bind("<FocusOut>", lambda event, e=entry: e.insert(0, "Bind a key") if e.get() == "" else None)

                entry.pack(side="right", padx=5)

                hotkey_entries[key] = entry

                ctk.CTkButton(self.settings_window, text="Apply", command=update_hotkeys, corner_radius=15).pack(pady=10)


if __name__ == "__main__":
                root = ctk.CTk()
                app = POESpeedrunTimer(root)
                root.mainloop()