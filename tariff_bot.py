import logging
import pandas as pd
import numpy as np

import small_talk

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    filename='tariff_bot_logger.txt',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, CHOOSING_SPHERE, CHOOSING_PERIOD, CHOOSING_FO, CHOOSING_REGION, TALKING = range(6)
main_reply_keyboard = [['Узнать тарифы'], ['Поговорить']]
#main_reply_keyboard = [['Узнать тарифы']]

data = pd.read_csv('tariff_data.csv')
if data.empty:
    data = pd.DataFrame()

def hello(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, hello: %s", user.username, user.id, update.message.text)
    update.message.reply_text(
        'Привет, ' + user.first_name + '! Я тарифный бот. Я знаю, какие тарифы установлены в сфере ЖКХ.\n',
        reply_markup=ReplyKeyboardMarkup(main_reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING

def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, start: %s", user.username, user.id, update.message.text)
    update.message.reply_text(
        reply_markup=ReplyKeyboardMarkup(main_reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CHOOSING

def talk(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, talk: %s", user.username, user.id, update.message.text)
    if (update.message.text == 'Узнать тарифы'):
        spheres = list(data.sphere.unique())
        context.user_data['spheres'] = spheres

        update.message.reply_text(
            'Выберите услугу ЖКХ:',
            reply_markup=ReplyKeyboardMarkup([[button] for button in spheres], one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOOSING_SPHERE
    else:
        responce = small_talk.get_responce(update.message.text)
        logger.info("user_name: %s, user_id: %s, responce: %s", user.username, user.id, responce)
        update.message.reply_text(
            responce,
            reply_markup=ReplyKeyboardMarkup([['Узнать тарифы']], one_time_keyboard=True, resize_keyboard=True)
            #reply_markup=ReplyKeyboardRemove()
        )
        return TALKING

def sphere(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, выбрано: %s", user.username, user.id, update.message.text)
    if (update.message.text == 'Узнать тарифы'):
        spheres = list(data.sphere.unique())
        context.user_data['spheres'] = spheres

        update.message.reply_text(
            'Выберите услугу ЖКХ:',
            reply_markup=ReplyKeyboardMarkup([[button] for button in spheres], one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOOSING_SPHERE
    else:
        return TALKING

def period(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, выбрана услуга: %s", user.username, user.id, update.message.text)

    sphere = update.message.text
    if sphere in context.user_data['spheres']:
        context.user_data['sphere'] = sphere
        periods = list(data[data.sphere == sphere].period.unique())
        context.user_data['periods'] = periods
        
        update.message.reply_text(
            'Выберите период:',
            reply_markup=ReplyKeyboardMarkup([[button] for button in periods], one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOOSING_PERIOD
    else:
        return


def fo(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, выбран период: %s", user.username, user.id, update.message.text)

    sphere = context.user_data['sphere']
    period = update.message.text
    if period in context.user_data['periods']:
        context.user_data['period'] = period
        fos = list(data[(data.sphere == sphere)&(data.period == period)].fo.unique())
        context.user_data['fos'] = fos
        
        update.message.reply_text(
            'Выберите федеральный округ:',
            reply_markup=ReplyKeyboardMarkup([[button] for button in fos], one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOOSING_FO
    else:
        return

def region(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, выбран ФО: %s", user.username, user.id, update.message.text)

    sphere = context.user_data['sphere']
    period = context.user_data['period']
    fo = update.message.text
    if fo in context.user_data['fos']:
        context.user_data['fo'] = fo
        regions = list(data[(data.sphere == sphere)&(data.period == period)&(data.fo == fo)].region.unique())
        context.user_data['regions'] = regions
        
        update.message.reply_text(
            'Выберите регион:',
            reply_markup=ReplyKeyboardMarkup([[button] for button in regions], one_time_keyboard=True, resize_keyboard=True),
        )
        return CHOOSING_REGION
    else:
        return

def tariff(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, выбран регион: %s", user.username, user.id, update.message.text)
    
    sphere = context.user_data['sphere']
    period = context.user_data['period']
    region = update.message.text

    if region in context.user_data['regions']:
        context.user_data['region'] = region

        cnt = len(data[(data.sphere == sphere)&(data.period == period)&(data.region == region)&(data.min_tar > 0)&(data.max_tar > 0)])
        min_tar = data[(data.sphere == sphere)&(data.period == period)&(data.region == region)].min_tar.min()
        max_tar = data[(data.sphere == sphere)&(data.period == period)&(data.region == region)].max_tar.max()
        context.user_data['min_tar'] = min_tar
        context.user_data['max_tar'] = max_tar        

        logger.info("user_name: %s, user_id: %s, сфера: %s, период: %s, регион: %s, мин.тариф: %s, макс.тариф: %s", user.username, user.id, context.user_data['sphere'], context.user_data['period'], context.user_data['region'], context.user_data['min_tar'], context.user_data['max_tar'])

        if ( cnt > 0 ):
            update.message.reply_text(
                'По данным раскрытия информации регулируемыми организациями в сфере ЖКХ:\n'
                'минимальный тариф - ' + str(min_tar) + (' руб./Гкал' if (sphere == 'Теплоснабжение') else ' руб./куб.м') + ',\n'
                'максимальный тариф - ' + str(max_tar) + (' руб./Гкал' if (sphere == 'Теплоснабжение') else ' руб./куб.м') + '.\n\n'
                'Нужна аналитика по данным в сфере тарифного регулирования?\n'
                'Компания "Платформа" сделает и автоматизирует с заботой о пользователе (https://data-platform.ru)\n',
                reply_markup=ReplyKeyboardMarkup(main_reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
            )
        else:
            update.message.reply_text(
                'Данные по тарифам с выбранными параметрами не найдены.\n'
                'Проверьте их наличие на федеральном портале раскрытия информации ЖКХ.\n\n'
                'Нужна аналитика по данным в сфере тарифного регулирования?\n'
                'Компания "Платформа" сделает и автоматизирует с заботой о пользователе (https://data-platform.ru)\n',
                reply_markup=ReplyKeyboardMarkup(main_reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
            )            
        return CHOOSING
    else:
        return

def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("user_name: %s, user_id: %s, cancel: %s", user.username, user.id, update.message.text)
    update.message.reply_text(
        'До встречи!', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    updater = Updater("1579408212:AAHNx_lZKXswfBMDrpR7bBPEfk_nM_a_7FQ")
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', hello)],
        states={
            CHOOSING: [MessageHandler(Filters.text & ~Filters.command, sphere)],
            CHOOSING_SPHERE: [MessageHandler(Filters.text & ~Filters.command, period)],
            CHOOSING_PERIOD: [MessageHandler(Filters.text & ~Filters.command, fo)],
            CHOOSING_FO: [MessageHandler(Filters.text & ~Filters.command, region)],
            CHOOSING_REGION: [MessageHandler(Filters.text & ~Filters.command, tariff)],
            TALKING: [MessageHandler(Filters.text & ~Filters.command, talk)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()