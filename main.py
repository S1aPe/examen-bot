import telebot
import matplotlib.pyplot as plt
from collections import defaultdict
import numpy as np

bot = telebot.TeleBot("7576409956:AAF4V9nLSi837tfd3HPlhKUqGEQ8_TsFN1k")

# Хранилище данных
user_data = defaultdict(lambda: {
    'income': 0.0,
    'expenses': defaultdict(float)
})

def create_combined_chart(chat_id):
    """Генерация комбинированного графика"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Данные
    income = user_data[chat_id]['income']
    expenses = user_data[chat_id]['expenses']
    total_expenses = sum(expenses.values())
    
    # График баланса
    bars = ax1.bar(['Доходы', 'Расходы'], [income, total_expenses],
                  color=['#4CAF50', '#F44336'], width=0.5)
    ax1.set_title('Общий баланс', pad=20, fontsize=14)
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, height,
                f'{height:.2f} руб',
                ha='center', va='bottom', fontsize=12)
    
    # Круговая диаграмма расходов
    if expenses:
        labels = []
        sizes = []
        for cat, amount in expenses.items():
            percentage = 100 * amount / total_expenses
            labels.append(f"{cat}\n({percentage:.1f}%)")
            sizes.append(amount)
        
        wedges, _, _ = ax2.pie(
            sizes, labels=labels, autopct=lambda p: '',
            colors=plt.cm.tab20.colors, startangle=90,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )
        
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1)/2 + wedge.theta1
            x = 0.7 * np.cos(np.deg2rad(angle))
            y = 0.7 * np.sin(np.deg2rad(angle))
            ax2.text(x, y, f"{sizes[i]:.0f} руб", 
                    ha='center', va='center', fontsize=10)
    else:
        ax2.text(0.5, 0.5, 'Нет данных', ha='center', va='center', fontsize=12)
    
    ax2.set_title('Расходы по категориям', pad=20, fontsize=14)
    ax2.axis('equal')
    
    plt.tight_layout()
    plt.savefig('chart.png', dpi=100)
    plt.close()
    return 'chart.png'

@bot.message_handler(commands=['start', 'help'])
def start(message):
    help_text = """
💰 <b>Финансовый помощник</b> 💰

Доступные команды:
/add_income [сумма] - добавить доход
/add_expense [категория] [сумма] - добавить расход (категория необязательна)
/report - показать отчёт
/clear - сбросить данные

Примеры:
/add_income 15000
/add_expense продукты 3500
/add_expense 2000 (добавится в категорию "другое")
/report
"""
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')

@bot.message_handler(commands=['add_income'])
def add_income(message):
    try:
        # Получаем сумму из сообщения
        amount = float(message.text.split()[1])
        chat_id = message.chat.id
        
        # Обновляем данные
        user_data[chat_id]['income'] += amount
        
        # Создаём и отправляем график
        chart = create_combined_chart(chat_id)
        with open(chart, 'rb') as photo:
            bot.send_photo(
                chat_id, photo,
                caption=f"✅ Добавлен доход: {amount:.2f} руб.\nОбщий доход: {user_data[chat_id]['income']:.2f} руб."
            )
    except IndexError:
        bot.reply_to(message, "❌ Укажите сумму!\nПример: /add_income 15000")
    except ValueError:
        bot.reply_to(message, "❌ Неверная сумма!\nИспользуйте числа, например: /add_income 15000")

@bot.message_handler(commands=['add_expense'])
def add_expense(message):
    try:
        # Разбираем команду
        parts = message.text.split()
        chat_id = message.chat.id
        
        # Определяем категорию и сумму
        if len(parts) == 2:  # Только сумма (/add_expense 100)
            category = "другое"
            amount = float(parts[1])
        elif len(parts) >= 3:  # Категория и сумма (/add_expense еда 100)
            category = parts[1]
            amount = float(parts[2])
        else:
            raise ValueError
        
        # Обновляем данные
        user_data[chat_id]['expenses'][category] += amount
        
        # Создаём и отправляем график
        chart = create_combined_chart(chat_id)
        with open(chart, 'rb') as photo:
            bot.send_photo(
                chat_id, photo,
                caption=f"💸 Добавлен расход: {category} -{amount:.2f} руб.\nВсего в категории: {user_data[chat_id]['expenses'][category]:.2f} руб."
            )
    except ValueError:
        bot.reply_to(message, "❌ Неверный формат!\nИспользуйте: /add_expense [категория] [сумма]\nИли просто: /add_expense [сумма]")

@bot.message_handler(commands=['report'])
def report(message):
    chat_id = message.chat.id
    income = user_data[chat_id]['income']
    expenses = user_data[chat_id]['expenses']
    total_expenses = sum(expenses.values())
    balance = income - total_expenses
    
    # Формируем текст отчёта
    report_text = f"""
📊 <b>Финансовый отчёт</b>
├ Доходы: {income:.2f} руб.
├ Расходы: {total_expenses:.2f} руб.
└ <b>Баланс</b>: {balance:.2f} руб.

🔍 <b>Детализация расходов:</b>
"""
    if expenses:
        for cat, amount in expenses.items():
            percentage = 100 * amount / total_expenses
            report_text += f"├ {cat}: {amount:.2f} руб. ({percentage:.1f}%)\n"
    else:
        report_text += "└ Нет данных о расходах\n"
    
    # Создаём и отправляем график
    chart = create_combined_chart(chat_id)
    with open(chart, 'rb') as photo:
        bot.send_photo(chat_id, photo, caption=report_text, parse_mode='HTML')

@bot.message_handler(commands=['clear'])
def clear(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'income': 0.0, 'expenses': defaultdict(float)}
    bot.send_message(chat_id, "♻️ Все данные были сброшены!")

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    bot.polling()