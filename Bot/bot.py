import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import asyncpg

# Настройки PostgreSQL и подключение к БД
DATABASE_URL = "postgresql://postgres:postpastmary@localhost:5432/HR_Department"

# Телеграм токен
BOT_TOKEN = "7581928679:AAGXyvoHb-_7O5jJECta2Yoejh26rS7l8iE"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Роли
ROLE_MANAGER = "HR"
ROLE_BOSS = "boss"

# Пользователи 
USERS = {
    "boss": {"password": "bossParol_123", "role": ROLE_BOSS},
    "HR": {"password": "HRParol_123", "role": ROLE_MANAGER},
}

# Состояния для работы с FSM
class Form(StatesGroup):
    login = State()
    add_worker = State()
    move_worker = State()
    fire_worker = State()
    view_statistics = State()
    view_report_card = State()
    add_order = State()

# Хранилище авторизационных данных
user_sessions = {}

# Меню
def get_keyboard_for_role(role: str) -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру верхнего уровня в зависимости от роли."""
    if role == ROLE_MANAGER:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Управление сотрудниками")],
                #[KeyboardButton(text="Рабочие процессы")],
                [KeyboardButton(text="Документы")],
                [KeyboardButton(text="Выход")],
            ],
            resize_keyboard=True
        )
    elif role == ROLE_BOSS:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Распоряжения")],
                [KeyboardButton(text="Посмотреть статистику")],
                [KeyboardButton(text="Выход")],
            ],
            resize_keyboard=True
        )

def get_return_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для возврата в главное меню."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Вернуться в главное меню")]],
        resize_keyboard=True
    )

def get_return2_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для возврата к меню."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Вернуться к меню")]],
        resize_keyboard=True
    )

@dp.message(lambda message: message.text == "Вернуться в главное меню")
async def return_to_main_menu_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    role = get_user_role(user_id)
    if role:
        keyboard = get_keyboard_for_role(role)
        await message.answer("Вы вернулись в главное меню.", reply_markup=keyboard)
        await state.clear()
    else:
        await message.answer("Вы не авторизованы. Введите /login для авторизации.")

@dp.message(lambda message: message.text == "Вернуться к меню")
async def return_to_menu_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    role = get_user_role(user_id)

    # Проверка роли и возврат соответствующего меню
    if role == ROLE_MANAGER:
        keyboard = get_employee_management_menu()  # Меню для HR-менеджера
    elif role == ROLE_BOSS:
        keyboard = get_boss_work_processes_menu()  # Меню для босса
    else:
        # Если роль не определена, можно вернуть какое-то дефолтное меню или сообщение об ошибке
        await message.answer("Ошибка! Неизвестная роль пользователя.", reply_markup=get_return_keyboard())
        return

    await message.answer("Вы вернулись к меню.", reply_markup=keyboard)
    await state.clear()

    

# Меню подуровней
def get_employee_management_menu() -> ReplyKeyboardMarkup:
    """Меню для управления сотрудниками."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Добавить сотрудника")],
            [KeyboardButton(text="Осуществление движения кадров")],
            [KeyboardButton(text="Ведение табеля")],
            [KeyboardButton(text="Вернуться в главное меню")],
        ],
        resize_keyboard=True
    )

def get_work_processes_menu() -> ReplyKeyboardMarkup:
    """Меню для рабочих процессов."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть распоряжения")],
            [KeyboardButton(text="Вернуться в главное меню")],
        ],
        resize_keyboard=True
    )

def get_boss_work_processes_menu() -> ReplyKeyboardMarkup:
    """Меню для рабочих процессов."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть распоряжения")],
            [KeyboardButton(text="Добавить распоряжение")],
            [KeyboardButton(text="Вернуться в главное меню")],
        ],
        resize_keyboard=True
    )

def get_general_menu() -> ReplyKeyboardMarkup:
    """Меню для общих действий."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Просмотреть распоряжения")],
            [KeyboardButton(text="Посмотреть статистику")],
            [KeyboardButton(text="Посмотреть табель")],
            [KeyboardButton(text="Вернуться в главное меню")],
        ],
        resize_keyboard=True
    )
@dp.message(lambda message: message.text == "Управление сотрудниками")
async def employee_management_handler(message: types.Message):
    await message.answer("Выберите действие для управления сотрудниками:", reply_markup=get_employee_management_menu())


@dp.message(lambda message: message.text == "Документы")
async def general_menu_handler(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=get_general_menu())

@dp.message(lambda message: message.text == "Распоряжения")
async def general_menu_handler(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=get_boss_work_processes_menu())

# Подключение к БД
async def init_db():
    return await asyncpg.create_pool(DATABASE_URL)

# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_sessions:
        role = user_sessions[user_id]["role"]
        keyboard = get_keyboard_for_role(role)
        await message.answer(f"Вы уже авторизованы как {role.capitalize()}.", reply_markup=keyboard)
    else:
        await message.answer("Добро пожаловать! Нажмите /login для авторизации.")


# Обработчик команды /login
@dp.message(Command("login"))
async def login_handler(message: types.Message, state: FSMContext):
    await message.answer("Введите логин и пароль через пробел (например, boss bossParol_123).")
    await state.set_state(Form.login)

@dp.message(Form.login)
async def process_login(message: types.Message, state: FSMContext):
    credentials = message.text.split()
    if len(credentials) != 2:
        await message.answer("Ошибка! Укажите логин и пароль через пробел.")
        return

    login, password = credentials
    user_data = USERS.get(login)

    if user_data and user_data["password"] == password:
        role = user_data["role"]
        user_sessions[message.from_user.id] = {"role": role}
        keyboard = get_keyboard_for_role(role)
        await message.answer(f"Успешная авторизация! Ваша роль: {role.capitalize()}.", reply_markup=keyboard)
        await state.clear()
    else:
        await message.answer("Неверный логин или пароль. Попробуйте снова.")


# Проверка роли пользователя
def get_user_role(user_id: int) -> str:
    session = user_sessions.get(user_id)
    return session["role"] if session else None

@dp.message(lambda message: message.text == "Выход")
async def logout_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]  # Удаляем данные пользователя из сессии
    await state.clear()  # Очищаем состояние FSM
    await message.answer("Вы вышли из системы. Введите /login для повторной авторизации.", reply_markup=types.ReplyKeyboardRemove())

# Добавление сотрудника (только для HR-специалиста)
@dp.message(lambda message: message.text == "Добавить сотрудника")
async def add_worker_handler(message: types.Message, state: FSMContext):
    if get_user_role(message.from_user.id) != ROLE_MANAGER:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите данные нового сотрудника в формате: ID, ФИО, паспорт, должность, ставка, зарплата, статус (например: A01, Иванов И.И., 1234567890, повар, 40, 100, works)",
        reply_markup=get_return2_keyboard()
        )
    await state.set_state(Form.add_worker)

@dp.message(Form.add_worker)
async def process_add_worker(message: types.Message, state: FSMContext):
    data = message.text.split(", ")
    if len(data) != 7:
        await message.answer("Ошибка! Проверьте формат ввода.")
        return
    worker_id, FCs, passport, profession, rate, salary, status = data

    try:
        rate = int(rate)  # Преобразуем rate в целое число
        salary = float(salary)  # Преобразуем salary в число с плавающей запятой
    except ValueError:
        await message.answer("Ошибка! Поля 'rate' и 'salary' должны быть числовыми значениями.")
        return

    pool = await init_db()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO worker (worker_id, FCs, passport, profession, rate, salary, status) 
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, worker_id, FCs, passport, profession, rate, salary, status)
            await message.answer(f"Сотрудник {FCs} успешно добавлен!")
        except Exception as e:
            await message.answer(f"Ошибка добавления: {e}")
    await state.clear()

# Перемещение сотрудника (только для менеджера)
@dp.message(lambda message: message.text == "Осуществление движения кадров")
async def move_worker_handler(message: types.Message, state: FSMContext):
    if get_user_role(message.from_user.id) != ROLE_MANAGER:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите ID сотрудника и новую должность (например, A01, отдел продаж, works)",
        reply_markup=get_return2_keyboard()
    )
    await state.set_state(Form.move_worker)

@dp.message(Form.move_worker)
async def process_move_worker(message: types.Message, state: FSMContext):
    data = message.text.split(", ")
    if len(data) != 3:
        await message.answer("Ошибка! Проверьте формат ввода.")
        return
    worker_id, profession, status = data
    pool = await init_db()
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                UPDATE worker SET profession = $2, status = $3 WHERE worker_id = $1
            """, worker_id, profession, status)
            await message.answer(f"Сотрудник {worker_id} перемещен в каткгорию {profession} со статусом {status}.")
        except Exception as e:
            await message.answer(f"Ошибка перемещения: {e}")
    await state.clear()

#kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk

# Добавление распоряжения (только для начальника)
@dp.message(lambda message: message.text == "Добавить распоряжение")
async def add_order_handler(message: types.Message, state: FSMContext):
    if get_user_role(message.from_user.id) != ROLE_BOSS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите распоряжение в формате: ID распоряжения, содержание, ID сотрудника (444, 2024-12-17, Уволить сотрудника Иванова И.И., A01).",
        reply_markup=get_return2_keyboard()
    )
    await state.set_state(Form.add_order)

from datetime import datetime

@dp.message(Form.add_order)
async def process_add_order(message: types.Message, state: FSMContext):
    data = message.text.split(", ")
    # Проверяем корректное количество данных
    if len(data) not in {3, 4}:
        await message.answer("Ошибка! Проверьте формат ввода. Ожидаемый формат: ID распоряжения, [дата], содержание, ID сотрудника.")
        return


    # Если дата указана
    if len(data) == 4:
        order_id, order_date, order_content, worker_id = data
        try:
            # Преобразуем дату из строки в объект datetime.date
            order_date = datetime.strptime(str(order_date).strip("'"), "%Y-%m-%d").date()
        except ValueError:
            await message.answer("Ошибка! Укажите дату в формате ГГГГ-ММ-ДД (например, 2024-12-17). " + str(order_date))
            return
    else:  # Если дата не указана, используется значение по умолчанию
        order_id, order_content, worker_id = data
        order_date = None



    pool = await init_db()
    async with pool.acquire() as conn:
        try:
            # Если дата указана
            if order_date:
                await conn.execute("""
                    INSERT INTO the_order (order_id, order_date, order_content, worker_id) 
                    VALUES ($1, $2, $3, $4)
                """, order_id, order_date, order_content, worker_id)
            else:  # Если дата не указана, используем значение по умолчанию
                await conn.execute("""
                    INSERT INTO the_order (order_id, order_content, worker_id) 
                    VALUES ($1, $2, $3)
                """, order_id, order_content, worker_id)

            await message.answer(f"Распоряжение {order_id} успешно добавлено для сотрудника {worker_id}.")
        except Exception as e:
            await message.answer(f"Ошибка добавления распоряжения: {e}")
    await state.clear()


# Просмотр распоряжений (только для менеджера)
@dp.message(lambda message: message.text == "Просмотреть распоряжения")
async def view_orders_handler(message: types.Message):


    pool = await init_db()
    async with pool.acquire() as conn:
        try:
            orders = await conn.fetch("""
                SELECT order_id, order_content, worker_id, order_date
                FROM the_order
                ORDER BY order_date DESC
            """)
            if not orders:
                await message.answer("Нет распоряжений.")
            else:
                orders_message = "\n".join(
                    [f"ID: {order['order_id']}\nДата: {order['order_date']}\nСотрудник: {order['worker_id']}\nСодержание: {order['order_content']}\n\n" for order in orders]
                )
                await message.answer(f"Распоряжения:\n{orders_message}")
        except Exception as e:
            await message.answer(f"Ошибка получения распоряжений: {e}")
#*88888888888888888888888888888888888888888888888888888888888

# Просмотр статистики (доступно для всех ролей)
@dp.message(lambda message: message.text == "Посмотреть статистику")
async def view_statistics_handler(message: types.Message):
    pool = await init_db()
    async with pool.acquire() as conn:
        try:
            # Выполняем запрос для получения работающих сотрудников
            workers_active = await conn.fetch("""
                SELECT worker_id, FCs, passport, profession, rate, salary, status
                FROM worker
                WHERE status = 'works'
                ORDER BY worker_id
            """)

            # Выполняем запрос для получения уволенных сотрудников
            workers_fired = await conn.fetch("""
                SELECT worker_id, FCs, passport, profession, rate, salary, status
                FROM worker
                WHERE status = 'fired'
                ORDER BY worker_id
            """)

            # Формируем сообщение для работающих сотрудников
            if workers_active:
                active_workers_message = "\n".join(
                    [
                        f"ID: {worker['worker_id']}\n"
                        f"ФИО: {worker['fcs']}\n"
                        f"Паспорт: {worker['passport']}\n"
                        f"Должность: {worker['profession']}\n"
                        f"Ставка: {worker['rate']} часов\n"
                        f"Зарплата: {worker['salary']} тыс.руб.\n"
                        #f"Статус: {worker['status']}\n"
                        for worker in workers_active
                    ]
                )
                active_workers_message = f"**Работающие сотрудники:**\n{active_workers_message}"
            else:
                active_workers_message = "Нет работающих сотрудников."

            # Формируем сообщение для уволенных сотрудников
            if workers_fired:
                fired_workers_message = "\n".join(
                    [
                        f"ID: {worker['worker_id']}\n"
                        f"ФИО: {worker['fcs']}\n"
                        f"Паспорт: {worker['passport']}\n"
                        f"Должность: {worker['profession']}\n"
                        f"Ставка: {worker['rate']} часов\n"
                        f"Зарплата: {worker['salary']} тыс.руб.\n"
                        #f"Статус: {worker['status']}\n"
                        for worker in workers_fired
                    ]
                )
                fired_workers_message = f"**Уволенные сотрудники:**\n{fired_workers_message}"
            else:
                fired_workers_message = "Нет уволенных сотрудников."

            # Отправляем сообщение пользователю
            await message.answer(f"{active_workers_message}\n\n{fired_workers_message}")

        except Exception as e:
            await message.answer(f"Ошибка получения статистики: {e}")


# Ведение табеля (только для менеджера)
@dp.message(lambda message: message.text == "Ведение табеля")
async def manage_report_card_handler(message: types.Message, state: FSMContext):
    if get_user_role(message.from_user.id) != ROLE_MANAGER:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите данные для табеля в формате: дата, ID сотрудника, ФИО, время входа (ЧЧ:ММ:СС), время выхода (ЧЧ:ММ:СС).\n"
        "Пример: 2024-11-20, A01, Иванов И.И., 08:30:00, 17:00:00",
        reply_markup=get_return2_keyboard()
    )
    await state.set_state(Form.fire_worker)


@dp.message(Form.fire_worker)
async def process_report_card_entry(message: types.Message, state: FSMContext):
    # Разделяем ввод на строки
    lines = message.text.strip().split("\n")
    pool = await init_db()
    errors = []
    success_count = 0

    async with pool.acquire() as conn:
        for line in lines:
            data = line.split(", ")
            if len(data) != 5:
                errors.append(f"Ошибка в строке: {line}. Ожидается 4 значений: дада, ID сотрудника, ФИО, время входа, время выхода.")
                continue

            date_of_report, worker_id, FCs, time_in, time_out = data

            try:
                # Преобразуем время входа и выхода в объекты datetime
                time_in = datetime.strptime(time_in, "%H:%M:%S")
                time_out = datetime.strptime(time_out, "%H:%M:%S")
                date_of_report = datetime.strptime(str(date_of_report).strip("'"), "%Y-%m-%d").date()
                # Проверяем, что время входа меньше времени выхода
                if time_in >= time_out:
                    errors.append(f"Ошибка в строке: {line}. Время входа должно быть меньше времени выхода.")
                    continue

                # Вставляем запись в таблицу табеля
                await conn.execute(
                    """
                    INSERT INTO report_card (date_of_report, worker_id, FCs, time_in, time_out)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    date_of_report, worker_id, FCs, time_in, time_out
                )
                success_count += 1

            except ValueError:
                errors.append(f"Ошибка в строке: {line}. Укажите время в формате ЧЧ:ММ:СС.")
            except Exception as e:
                errors.append(f"Ошибка в строке: {line}. {e}")

    # Отправляем пользователю отчет по обработке
    if success_count > 0:
        await message.answer(f"Успешно добавлено {success_count} записей в табель.")
    if errors:
        await message.answer("Произошли ошибки:\n" + "\n".join(errors))

    await state.clear()

############################
# Функция для получения табеля по всем сотрудникам, сгруппированного по дням
@dp.message(lambda message: message.text == "Посмотреть табель")
async def view_report_card_handler(message: types.Message):
    try:
        # Подключение к базе данных
        pool = await init_db()
        async with pool.acquire() as conn:
            # Запрос на получение данных
            query = """
            SELECT date_of_report, worker_id, FCs, time_in, time_out
            FROM report_card
            ORDER BY date_of_report, worker_id
            """
            records = await conn.fetch(query)  # Получаем все записи

            # Логируем количество записей
            print(f"Записей найдено: {len(records)}")
        
        if not records:  # Если нет данных
            await message.answer("Нет данных по табелям для сотрудников.")
            return

        # Формирование отчета
        report = "Табель по дням для всех сотрудников:\n                                      ID           ФИО            Время вх.         Время вых."
        current_date = None  # Для отслеживания изменений даты

        for record in records:
            date_of_report = record['date_of_report']
            worker_id = record['worker_id']
            FCs = record['fcs']
            time_in = record['time_in']
            time_out = record['time_out']
            
            # Если дата изменилась, выводим новый заголовок для нового дня
            if date_of_report != current_date:
                if current_date is not None:
                    report += "\n"  # Добавляем разделение между днями
                report += f"\nДата: {date_of_report}\n"
                current_date = date_of_report

            # Добавляем информацию о работнике
            report += f"                                 {worker_id},     {FCs},        {time_in},           {time_out}\n"
            print({report}) 
        # Отправляем отчет пользователю
        await message.answer(report)

    except Exception as e:
        # Логируем ошибки
        print(f"Произошла ошибка: {str(e)}")
        await message.answer("Произошла ошибка при получении данных.")


    


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
