import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
import requests
from bs4 import BeautifulSoup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config_data.config import Config, load_config
from aiogram.types.input_file import FSInputFile
from keyboards.keyboard import html_keyboard
from lexicon.lexicon import LEXICON_RU

config: Config = load_config()
bot = Bot(token=config.tg_bot.token)

class Link(StatesGroup):
    link = State()
router = Router()

@router.message(Command(commands=['start']))
async def process_start_command(message: Message):
    await message.answer(LEXICON_RU['/start'],
    reply_markup = html_keyboard)

@router.message(F.text == 'Приступить к работе')
async def get_link(message: Message, state: FSMContext):
    await state.set_state(Link.link)
    await message.answer('Используйте команду /route для получения маршрута.')
@router.message(Command("route"))
async def get_route(message: Message):
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer(
            "Пожалуйста, укажите координаты начальной и конечной точек в формате: /route lat1,long1 lat2,long2")
        return

    start_point = args[0]
    end_point = args[1]

    # Формируем URL для парсинга
    url = f"https://yandex.ru/maps/?ll={start_point}&mode=routes&rtext={start_point}~{end_point}&rtt=pd&ruri=~&z=18.24"
    # Замените на реальный URL для парсинга
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Здесь нужно использовать правильные селекторы для извлечения данных о маршруте
        try:
            distance = soup.select_one('.pedestrian-route-snippet-view__route-title-secondary').text
            duration = soup.select_one('.pedestrian-route-snippet-view__route-title-primary').text
            await message.answer(f'Маршрут найден! Дистанция: {distance}, Время в пути: {duration}.Ccылка: {url}')
        except AttributeError:
            await message.answer('Не удалось извлечь информацию о маршруте.')
    else:
        await message.answer(f'Ошибка при запросе: {response.status_code}')

    def fetch_data(url):
        count = 0
        while True:
            scripts = soup.find_all('script', class_="state-view")

            if scripts:
                return scripts[0].string  # Предполагаем, что нужные данные в первом найденном скрипте

            count += 1
            print("Попытка получить данные: ", count)

    def extract_coordinates(content, output_file):
        start_marker = '"coordinates":[['
        end_marker = ']]}'

        start_index = content.find(start_marker)
        end_index = content.find(end_marker, start_index)

        if start_index != -1 and end_index != -1:
            start_index += len(start_marker)
            coordinates_data = content[start_index:end_index].strip()

            # Убираем квадратные скобки и запятые, а затем разбиваем на строки
            coordinates_data = coordinates_data.replace('[', '').replace(']', '').replace(',', '\n').strip()

            with open(output_file, 'w', encoding='utf-8') as outfile:
                outfile.write(coordinates_data)

            print(f"Координаты успешно извлечены и записаны в файл {output_file}.")
        else:
            print("Не удалось найти координаты в данных.")

    def edit_file(search_string, file_name):
        with open(file_name, 'r', encoding="utf-8") as file:
            lines = file.readlines()

        filtered_lines = [line for line in lines if search_string in line]

        if filtered_lines:
            with open(file_name, 'w', encoding="utf-8") as file:
                file.writelines(filtered_lines)
        else:
            print("Строки не найдены.")


    # Основной код
    url = f"https://yandex.ru/maps/?ll={start_point}&mode=routes&rtext={start_point}~{end_point}&rtt=pd&ruri=~&z=18.24"
    file_name = f"1.txt"

    # Получаем данные с URL
    data = fetch_data(url)

    # Записываем полученные данные в файл
    with open(file_name, 'w', encoding="utf-8") as file:
        file.write(data)

    print(f"Данные успешно записаны в файл {file_name}.")

    # Извлекаем координаты из файла
    extract_coordinates(data, file_name)

    import xml.etree.ElementTree as ET

    def convert_to_gpx(input_file, output_file):
        # Создаем корневой элемент GPX
        gpx = ET.Element('gpx', version='1.1', creator='YourName')

        with open(input_file, 'r') as file:
            lines = file.readlines()

            # Обрабатываем координаты
            for i in range(0, len(lines), 2):  # Проходим по строкам с шагом 2
                if i + 1 < len(lines):  # Проверяем, чтобы не выйти за пределы списка
                    longitude = lines[i].strip()  # Долгота
                    latitude = lines[i + 1].strip()  # Широта

                    # Создаем элемент "wpt" (waypoint) для каждой пары координат
                    wpt = ET.SubElement(gpx, 'wpt', lat=latitude, lon=longitude)
                    ET.SubElement(wpt, 'name').text = f'Point {i // 2 + 1}'  # Имя точки

        # Записываем GPX в файл
        tree = ET.ElementTree(gpx)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)

        print(f"GPX файл успешно создан: {output_file}")

    # Основной код
    input_file = f'1.txt'  # Имя входного текстового файла с координатами
    output_file = f'route.gpx' # Имя выходного GPX файла

    convert_to_gpx(input_file, output_file)
    user_id = message.from_user.id
    document = FSInputFile(f'route.gpx')
    await bot.send_document(user_id, document, caption=f'Ваш GPX-файл!')
    os.remove(f'1.txt')
    os.remove(f'route.gpx')


# Обработчик команды /help
@router.message(Command(commands=["help"]))
async def start_command(message:Message):
    await message.answer(text=LEXICON_RU['/help'], reply_markup=html_keyboard, parse_mode="HTML")