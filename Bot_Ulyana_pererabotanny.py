# Импортируем необходимые классы.
from io import BytesIO
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
import requests

# Токен для доступа к чату
TOKEN = '1719119532:AAFcxjiUeROK2PK6UyJ18v7AxDZU1qSIO8U'

# Клавиатура
reply_keyboard = [['/next', '/later']]

# Событие вызова клавиатуры
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)


# Функция, вызываемая командой /start
def start(update, context):
    update.message.reply_text(
        "Clikk - бот для поиска самых красивых и уютных ресторанов (кафе) со вкусной едой в любой точке мира.\n"
        "Чтобы продолжить общение с ботом воспользуйтесь командой /help, изучите инструкцию и начните работу.")


# Функция, вызываемая командой /help
def help(update, context):
    text = [
        "Этот бот поможет найти хорошее место для семейного ужина, свидания или случайного перекуса во время прогулки.",
        "Стоит только написать своё место положения, и вы увидите подходящие варианты.",
        "На ниже появившейся кнопке выберете дальнейшее действие:",
        "/next - вы начинаете поиск ресторана (кафе);",
        "/later - вы завершите работу с ботом на данный момент и сможете её продолжить позже.\n"
        "Если вы  хотите завершить работу с ботом, то напишите /stop в любой момент работы с ботом."
    ]
    update.message.reply_text('\n'.join(text), reply_markup=markup)


def close_keyboard_1(update, context):
    update.message.reply_text(
        "Я буду рад помочь вам в вашем поиске.",
        reply_markup=ReplyKeyboardRemove()
    )
    update.message.reply_text(
        "Напишите своё местоположение.\n"
        "Например: Воронеж, улица Хользунова.\n"
        "* улицу стоит уточнять, так как тогда место для вашего отдыха будет искаться"
        " в определённом районе, а не во всём городе."
    )
    return 1


def get_geocoder_data(address):
    # geocoder api
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    # Параметры запроса
    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": address,
        "format": "json"}

    # Совершаем запрос
    response = requests.get(geocoder_api_server, params=geocoder_params)

    # Если ответ пуст
    if not response:
        return None

    # Преобразуем ответ в json-объект
    json_response_1 = response.json()

    # Получаем координаты нужного места из ответа
    ll = json_response_1['response']['GeoObjectCollection']['featureMember'][0]
    ll = ll['GeoObject']['Point']['pos']
    return ','.join(ll.split())


def search_organizations(ll, text):
    # Api для поиска по организациям
    search_api_server = "https://search-maps.yandex.ru/v1/"

    # Ключ к api
    api_key = "fc24761c-ed09-4b53-860f-05e1c93e3830"

    # Параметры запроса
    search_params = {
        "apikey": api_key,
        "text": text,
        "lang": "ru_RU",
        "ll": ll,
        "type": "biz"
    }

    # Совершаем запрос
    response = requests.get(search_api_server, params=search_params)

    # Преобразуем ответ в json-объект
    json_response_2 = response.json()

    # Получаем все нужные организации, которые удалось найти
    organizations = json_response_2["features"]
    return organizations


def first_response(update, context):
    # Это ответ на первый вопрос.
    # Мы можем использовать его во втором вопросе.
    locality = update.message.text
    if locality == '/stop':
        update.message.reply_text(
            "Вы завершили работу с ботом, надеемся что скоро вернётесь к общению.")
        # Заканчиваем сценарий
        return ConversationHandler.END
    update.message.reply_text(
        "Поиск подходящих мест по адресу: '{locality}' начат.".format(**locals()))

    # Получаем координаты места
    ll = get_geocoder_data(locality)

    # Получаем все организации, находящиеся рядом с местом
    orgs = search_organizations(ll, "кафе")

    # Получаем названия организаций.
    org_names = [i["properties"]["CompanyMetaData"]["name"] for i in orgs]

    # Получаем адресы организаций.
    org_addresses = [i["properties"]["CompanyMetaData"]["address"] for i in orgs]

    # Получаем координаты организаций.
    points = [i["geometry"]["coordinates"] for i in orgs]
    org_points = [f"{point[0]},{point[1]},pm2dgl" for point in points]
    delta = "0.006"

    # Добавляем на карту метку, означающую место, чтобы было нагляднее
    org_points.append(f'{ll},pm2rdl')

    # Собираем параметры для запроса к StaticMapsAPI:
    map_params = {
        # позиционируем карту центром на наш исходный адрес
        "ll": ll,
        "spn": ",".join([delta, delta]),
        "l": "map",
        "pt": '~'.join(org_points)
    }
    map_api_server = "http://static-maps.yandex.ru/1.x/"
    response = requests.get(map_api_server, params=map_params)

    # Генерируем текст, который хотим вывести
    text = [
        "Нашел!", "Красная метка - вы, а зеленые - кафе.", "Вот список всез ресторанов поблизости:",
        "\n".join([f'    {i + 1}) {org_names[i]}' for i in range(len(org_names))])
    ]
    # Отсылаем изображение в чат
    context.bot.send_photo(update.message.chat_id, BytesIO(response.content), caption='\n'.join(text))
    if locality == '/stop':
        # Заканчиваем сценарий
        return ConversationHandler.END


def stop(update, context):
    update.message.reply_text(
        "Вы прервали общение с ботом."
    )


def close_keyboard_2(update, context):
    update.message.reply_text(
        "Возвращайтесь позже. Надеюсь потом я смогу вам чем-либо помочь.",
        reply_markup=ReplyKeyboardRemove()
    )


# Сценарий поиска кафе
conv_handler = ConversationHandler(
    # Точка входа в диалог.
    # В данном случае — команда /next. Она задаёт первый вопрос.
    entry_points=[CommandHandler('next', close_keyboard_1)],
    states={
        # Функция читает ответ на первый вопрос и задаёт второй.
        1: [MessageHandler(Filters.text, first_response)]
    },

    # Точка прерывания диалога. В данном случае — команда /stop.
    fallbacks=[CommandHandler('stop', stop)]
)


def main():
    # Создаём объект updater.
    updater = Updater(TOKEN, use_context=True)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # Зарегистрируем команды, на которые будет реагировать бот
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("later", close_keyboard_2))
    dp.add_handler(CommandHandler("stop", stop))

    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
