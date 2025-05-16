import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import random
import sqlite3
from AnekdotDop import safe_exit

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('anekdots.db')
cursor = conn.cursor()

# Создаем таблицу для анекдотов, если она еще не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS anekdots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        rating INTEGER
    )
''')
conn.commit()

def get_anekdots(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        messagebox.showerror("Ошибка", f"Не удалось загрузить анекдоты. Код: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    jokes_html = soup.find_all("div", class_="text")
    jokes = [joke.get_text(strip=True) for joke in jokes_html]

    # Сохраняем анекдоты в базе данных
    for joke in jokes:
        cursor.execute('''
            INSERT INTO anekdots (text, rating) VALUES (?, ?)
        ''', (joke, None))  # Начальная оценка = None
    conn.commit()

    # Загружаем все анекдоты и сортируем их по оценке
    cursor.execute('''
        SELECT text, rating FROM anekdots ORDER BY rating DESC
    ''')
    sorted_jokes = cursor.fetchall()

    # Преобразуем результат в список только с текстами анекдотов
    sorted_jokes = [joke[0] for joke in sorted_jokes]
    
    random.shuffle(sorted_jokes)  # Перемешиваем анекдоты (если хотите случайный порядок)
    return sorted_jokes

def show_next_joke():
    global index
    if index < len(anekdots):
        joke_text.config(state=tk.NORMAL)
        joke_text.delete("1.0", tk.END)
        joke_text.insert(tk.END, f"Анекдот {index + 1}:\n\n{anekdots[index]}")
        joke_text.config(state=tk.DISABLED)
        
        # Сбросить звездную оценку
        rating_label.config(text="Оцените анекдот: gfdfgdfgd")
        for btn in rating_buttons:
            btn.config(state=tk.NORMAL)

        index += 1
    else:
        messagebox.showinfo("Конец", "Анекдоты закончились!")
        safe_exit(conn, root)

def rate_joke(rating):
    global index
    # Записываем оценку в базу данных для текущего анекдота
    cursor.execute('''
        UPDATE anekdots
        SET rating = ?
        WHERE text = ?
    ''', (rating, anekdots[index]))
    conn.commit()
    
    # Отображаем оценку
    rating_label.config(text=f"Вы поставили {rating} звезд(ы)")
    
    # Отключаем кнопки после того, как пользователь поставил оценку
    for btn in rating_buttons:
        btn.config(state=tk.DISABLED)
    
    # Переход к следующему анекдоту после небольшой задержки
    root.after(1000, show_next_joke)

def filter_by_rating(min_rating):
    # Получаем анекдоты с фильтром по минимальной оценке
    cursor.execute('''
        SELECT text, rating FROM anekdots WHERE rating >= ? ORDER BY rating DESC
    ''', (min_rating,))
    filtered_jokes = cursor.fetchall()

    # Преобразуем результат в список только с текстами анекдотов
    filtered_jokes = [joke[0] for joke in filtered_jokes]

    return filtered_jokes

def show_filtered_jokes(min_rating):
    global anekdots, index
    # Фильтруем анекдоты по оценке
    anekdots = filter_by_rating(min_rating)
    index = 0  # Сбросим индекс для новых фильтрованных анекдотов
    if anekdots:
        show_next_joke()
    else:
        joke_text.config(state=tk.NORMAL)
        joke_text.delete("1.0", tk.END)
        joke_text.insert(tk.END, "Нет анекдотов с такой оценкой.")
        joke_text.config(state=tk.DISABLED)

# Получаем анекдоты
url = "https://www.anekdot.ru/release/anekdot/day/2025-04-23/"
anekdots = get_anekdots(url)
index = 0

if anekdots:
    # Создание окна
    root = tk.Tk()
    root.title("Анекдоты дня смейся если ты не пидор")
    root.geometry("700x400")

    # Основной фрейм
    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Создание вкладок
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)

    # Вкладка с анекдотами
    joke_tab = ttk.Frame(notebook)
    notebook.add(joke_tab, text="Все анекдоты")

    # Вкладка с фильтром по оценке
    filter_tab = ttk.Frame(notebook)
    notebook.add(filter_tab, text="Фильтровать по оценке")

    # Текстовое поле
    joke_text = tk.Text(joke_tab, wrap=tk.WORD, font=("Arial", 12), bg="#fdfdfd", height=10)
    joke_text.pack(fill=tk.BOTH, expand=True)

    # Кнопка "Следующий анекдот"
    next_button = tk.Button(joke_tab,
                            text="Следующий анекдот 👉",
                            command=show_next_joke,
                            font=("Arial", 12, "bold"),
                            bg="#dff0d8")
    next_button.pack(pady=10)

    # Место для отображения рейтинга
    rating_label = tk.Label(joke_tab, text="Оцените анекдот:", font=("Arial", 12))
    rating_label.pack()

    # Кнопки для оценки (от 1 до 5 звезд)
    rating_buttons = []
    for i in range(1, 6):
        btn = tk.Button(joke_tab, text=f"{i}⭐", font=("Arial", 12), command=lambda i=i: rate_joke(i))
        btn.pack(side=tk.LEFT, padx=5)
        rating_buttons.append(btn)

    # Фильтр по оценке
    filter_label = tk.Label(filter_tab, text="Минимальная оценка:", font=("Arial", 12))
    filter_label.pack(pady=10)

    # Кнопки фильтрации
    filter_buttons = []
    for i in range(1, 6):
        btn = tk.Button(filter_tab, text=f"Оценка {i}⭐", font=("Arial", 12), command=lambda i=i: show_filtered_jokes(i))
        btn.pack(side=tk.LEFT, padx=5)
        filter_buttons.append(btn)

    # Показываем первый анекдот
    show_next_joke()

    # Запуск окна
    root.mainloop()
else:
    print("Анекдоты не найдены.")

# Закрываем соединение с базой данных

