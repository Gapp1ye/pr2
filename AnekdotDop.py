import sqlite3
import sys
from tkinter import messagebox

def safe_exit(connection=None, root=None, show_message=True):
    """
    Завершает приложение безопасно: закрывает соединение и окно.
    """
    try:
        if connection:
            connection.close()
        if root:
            root.destroy()
        if show_message:
            messagebox.showinfo("Выход", "Программа завершена.")
    except Exception as e:
        print(f"Ошибка при завершении: {e}")
    finally:
        sys.exit()