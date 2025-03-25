import os
import psycopg2
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# Load the environment variable for Neon PostgreSQL connection
database_url = os.getenv('postgresql://neondb_owner:npg_soDn7mHl2xJf@ep-red-haze-a85ugmii-pooler.eastus2.azure.neon.tech/neondb?sslmode=require')

# Проверка, что строка подключения получена
print(f"Database URL: {database_url}")

# Connect to the Neon PostgreSQL database
conn = psycopg2.connect("dbname='neondb' user='neondb_owner' password='npg_soDn7mHl2xJf' host='ep-red-haze-a85ugmii-pooler.eastus2.azure.neon.tech' port='5432' sslmode='require'")

c = conn.cursor()

# Создаем таблицы для хранения данных
c.execute('''CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    amount REAL,
    category TEXT,
    date TEXT
)''')
c.execute('''CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
)''')
c.execute('''CREATE TABLE IF NOT EXISTS finance_info (
    id SERIAL PRIMARY KEY,
    balance REAL,
    expenses_total REAL
)''')
conn.commit()

# Глобальные переменные для баланса и расходов
balance = 0.0
expenses_total = 0.0

def load_finance_info():
    global balance, expenses_total
    c.execute("SELECT * FROM finance_info WHERE id = 1")
    row = c.fetchone()
    if row:
        balance, expenses_total = row[1], row[2]
    else:
        balance, expenses_total = 0.0, 0.0
        c.execute("INSERT INTO finance_info (balance, expenses_total) VALUES (%s, %s)", (balance, expenses_total))
        conn.commit()

def save_finance_info():
    global balance, expenses_total
    c.execute("UPDATE finance_info SET balance = %s, expenses_total = %s WHERE id = 1", (balance, expenses_total))
    conn.commit()

def update_display():
    global balance, expenses_total
    lbl_balance.config(text=f"Общий баланс: {balance:.2f} сом")
    lbl_expenses.config(text=f"Общие траты: {expenses_total:.2f} сом")

def update_balance():
    def save_balance():
        global balance
        new_balance = entry_balance.get()
        try:
            balance = float(new_balance)
            save_finance_info()  # Сохраняем изменения в базе
            update_display()
            balance_window.destroy()
        except ValueError:
            messagebox.showwarning("Ошибка", "Некорректный ввод!")
    
    balance_window = tk.Toplevel(root)
    balance_window.title("Редактировать баланс")
    balance_window.geometry("380x200")
    ttk.Label(balance_window, text="Введите новый баланс:", font=("Arial", 16)).pack(pady=16)
    entry_balance = ttk.Entry(balance_window)
    entry_balance.pack(pady=10)
    ttk.Button(balance_window, text="Сохранить", command=save_balance).pack(pady=10)

def add_category():
    def save_category():
        category = entry_category.get()
        if category:
            try:
                c.execute("INSERT INTO categories (name) VALUES (%s)", (category,))
                conn.commit()
                category_window.destroy()
                update_category_list()
            except psycopg2.IntegrityError:
                messagebox.showwarning("Ошибка", "Такая категория уже существует!")
        else:
            messagebox.showwarning("Ошибка", "Введите название категории!")
    
    category_window = tk.Toplevel(root)
    category_window.title("Добавить категорию")
    category_window.geometry("380x200")
    ttk.Label(category_window, text="Введите категорию:", font=("Arial", 16)).pack(pady=16)
    entry_category = ttk.Entry(category_window)
    entry_category.pack(pady=10)
    ttk.Button(category_window, text="Добавить", command=save_category).pack(pady=10)

def delete_category():
    selected_item = category_tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите категорию для удаления!")
        return
    
    item = category_tree.item(selected_item)
    category_id = item["values"][0]
    c.execute("DELETE FROM categories WHERE id = %s", (category_id,))
    conn.commit()
    update_category_list()

# Глобальная переменная для хранения списка категорий
category_tree = None  

def update_category_list():
    """Обновляет список категорий в дереве"""
    global category_tree  
    if category_tree is None:
        return  # Если окно категорий ещё не открыто, выходим из функции
    
    # Очищаем текущие записи в Treeview
    category_tree.delete(*category_tree.get_children())  
    
    # Запрашиваем список категорий из базы данных
    c.execute("SELECT id, name FROM categories")
    rows = c.fetchall()
    
    # Заполняем дерево категориями
    for row in rows:
        category_tree.insert("", "end", values=row)

def update_table():
    tree.delete(*tree.get_children())
    c.execute("SELECT * FROM expenses")
    for row in c.fetchall():
        tree.insert("", "end", values=row)

def delete_expense():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите запись для удаления!")
        return
    item = tree.item(selected_item)
    expense_id = item["values"][0]
    c.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    conn.commit()
    update_table()

def add_expense():
    def save_expense():
        global balance, expenses_total
        amount = entry_amount.get()
        category = category_var.get()
        date = datetime.now().strftime("%Y-%m-%d")

        if not amount or not category:
            messagebox.showwarning("Ошибка", "Введите сумму и выберите категорию!")
            return
        
        try:
            amount = float(amount)
            balance -= amount
            expenses_total += amount
            save_finance_info()  # Сохраняем изменения в базе
            c.execute("INSERT INTO expenses (amount, category, date) VALUES (%s, %s, %s)", (amount, category, date))
            conn.commit()
            update_table()
            update_display()
            expense_window.destroy()
        except ValueError:
            messagebox.showwarning("Ошибка", "Некорректная сумма!")
    
    expense_window = tk.Toplevel(root)
    expense_window.title("Добавить расход")
    expense_window.geometry("500x300")
    ttk.Label(expense_window, text="Введите сумму:").pack(pady=5)
    entry_amount = ttk.Entry(expense_window)
    entry_amount.pack(pady=5)
    ttk.Label(expense_window, text="Выберите категорию:").pack(pady=5)
    category_var = tk.StringVar()
    c.execute("SELECT name FROM categories")
    categories = [row[0] for row in c.fetchall()]
    category_menu = ttk.Combobox(expense_window, textvariable=category_var, values=categories, state="readonly")
    category_menu.pack(pady=5)
    ttk.Button(expense_window, text="Добавить", command=save_expense).pack(pady=10)

def edit_expense():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Ошибка", "Выберите запись для редактирования!")
        return
    
    item = tree.item(selected_item)
    expense_id, amount, category, date = item["values"]
    
    def save_changes():
        new_amount = entry_amount.get()
        new_category = category_var.get()
        
        try:
            new_amount = float(new_amount)
            c.execute("UPDATE expenses SET amount = %s, category = %s WHERE id = %s", (new_amount, new_category, expense_id))
            conn.commit()
            update_table()
            edit_window.destroy()
        except ValueError:
            messagebox.showwarning("Ошибка", "Некорректная сумма!")
    
    edit_window = tk.Toplevel(root)
    edit_window.title("Редактировать расход")
    edit_window.geometry("300x200")
    ttk.Label(edit_window, text="Введите сумму:").pack(pady=5)
    entry_amount = ttk.Entry(edit_window)
    entry_amount.insert(0, amount)
    entry_amount.pack(pady=5)
    ttk.Label(edit_window, text="Выберите категорию:").pack(pady=5)
    category_var = tk.StringVar(value=category)
    c.execute("SELECT name FROM categories")
    categories = [row[0] for row in c.fetchall()]
    category_menu = ttk.Combobox(edit_window, textvariable=category_var, values=categories, state="readonly")
    category_menu.pack(pady=5)
    ttk.Button(edit_window, text="Сохранить", command=save_changes).pack(pady=10)

root = tk.Tk()
root.title("Мои финансы")
root.geometry("600x700")
root.configure(bg="#DCC6E0")

lbl_title = ttk.Label(root, text="МОИ ФИНАНСЫ", font=("Arial", 18, "bold"), background="#DCC6E0", foreground="#4A235A")
lbl_title.pack(pady=10)

lbl_balance = ttk.Label(root, text="Общий баланс: 0.00 сом", font=("Arial", 14, "bold"), background="#DCC6E0", foreground="#4A235A")
lbl_balance.pack(pady=5)

lbl_expenses = ttk.Label(root, text="Общие траты: 0.00 сом", font=("Arial", 14, "bold"), background="#DCC6E0", foreground="#4A235A")
lbl_expenses.pack(pady=5)

frame_buttons = tk.Frame(root, bg="#DCC6E0")
frame_buttons.pack(pady=10)
btn_edit_balance = ttk.Button(frame_buttons, text="Редактировать баланс", command=update_balance)
btn_edit_balance.pack(side="left", padx=10)
btn_category_list = ttk.Button(frame_buttons, text="Категории", command=lambda: open_category_window())
btn_category_list.pack(side="left", padx=10)

# Функция для отображения окна с категориями
def open_category_window():
    """Открывает окно с категориями"""
    global category_tree  
    category_window = tk.Toplevel(root)
    category_window.title("Категории")
    category_window.geometry("380x400")

    # Вставляем кнопки внутри окна категорий
    frame_buttons = tk.Frame(category_window, bg="#DCC6E0")
    frame_buttons.pack(pady=10)

    btn_add_category = ttk.Button(frame_buttons, text="Добавить категорию", command=add_category)
    btn_add_category.pack(side="left", padx=10)

    btn_delete_category = ttk.Button(frame_buttons, text="Удалить категорию", command=delete_category)
    btn_delete_category.pack(side="left", padx=10)

    # Создание списка категорий
    category_tree = ttk.Treeview(category_window, columns=("ID", "Категория"), show="headings", height=10)
    category_tree.heading("ID", text="ID")
    category_tree.heading("Категория", text="Категория")
    category_tree.pack(pady=10)

    update_category_list()  # Обновляем список категорий после создания окна


# Основное окно для расходов
tree = ttk.Treeview(root, columns=("ID", "Сумма", "Категория", "Дата"), show="headings")
tree.heading("ID", text="ID")
tree.heading("Сумма", text="Сумма")
tree.heading("Категория", text="Категория")
tree.heading("Дата", text="Дата")
tree.pack(pady=10)

frame_buttons = tk.Frame(root, bg="#DCC6E0")
frame_buttons.pack(pady=10)
btn_add_expense = ttk.Button(frame_buttons, text="Добавить расход", command=add_expense)
btn_add_expense.pack(side="left", padx=10)
btn_edit = ttk.Button(frame_buttons, text="Редактировать расход", command=edit_expense)
btn_edit.pack(side="left", padx=10)
btn_delete = ttk.Button(frame_buttons, text="Удалить расход", command=delete_expense)
btn_delete.pack(side="left", padx=10)

load_finance_info()
update_display()
update_table()
update_category_list()

root.mainloop()

conn.close()
c.close()
