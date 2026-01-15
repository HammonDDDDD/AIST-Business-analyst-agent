import os
import telebot
from dotenv import load_dotenv
from graph import compile_graph

load_dotenv()

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
if not TG_TOKEN:
    print("Не задан TG_BOT_TOKEN в .env или коде")
    exit()

bot = telebot.TeleBot(TG_TOKEN)
app = compile_graph()

user_sessions = {}


def render_markdown(artifact: dict) -> str:
    """Генерация текста для сохранения в файл (полный Markdown)"""
    if not artifact: return "Нет данных"

    title = artifact.get('title', artifact.get('project_name', 'Проект'))
    text = f"# {title}\n\n"
    text += f"## Описание\n{artifact.get('description', '')}\n\n"
    text += "## Цели\n" + "\n".join([f"- {g}" for g in artifact.get('goals', [])]) + "\n\n"
    text += "## Функциональные требования\n"

    reqs = artifact.get('functional_requirements') or artifact.get('requirements') or []
    for r in reqs:
        r_id = r.get('id') if isinstance(r, dict) else getattr(r, 'id', 'N/A')
        r_desc = r.get('description') if isinstance(r, dict) else getattr(r, 'description', '')
        text += f"- **{r_id}**: {r_desc}\n"

    return text


def render_message_text(artifact: dict) -> str:
    """Генерация текста для сообщения в Telegram (упрощенное форматирование)"""
    if not artifact: return "⚠️ Данные отсутствуют."

    title = artifact.get('title', artifact.get('project_name', 'Проект'))

    msg = f"📋 **{title}**\n\n"
    msg += f"ℹ️ *Описание:*\n{artifact.get('description', 'Не указано')}\n\n"

    msg += "🎯 *Цели:*\n"
    for g in artifact.get('goals', []):
        msg += f"— {g}\n"

    msg += "\n⚙️ *Требования:*\n"
    reqs = artifact.get('functional_requirements') or artifact.get('requirements') or []

    for r in reqs:
        r_id = r.get('id') if isinstance(r, dict) else getattr(r, 'id', 'N/A')
        r_desc = r.get('description') if isinstance(r, dict) else getattr(r, 'description', '')
        msg += f"• *{r_id}*: {r_desc}\n"

    return msg


@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_sessions[chat_id] = {"is_active": False, "thread_id": str(chat_id)}

    bot.reply_to(message,
                 "👋 Привет! Я AI-Бизнес-аналитик.\n\n"
                 "Напиши мне идею своего проекта (например: 'Хочу сервис доставки еды дронами'), "
                 "и я подготовлю ТЗ с функциональными требованиями.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_text = message.text.strip()

    if chat_id not in user_sessions:
        user_sessions[chat_id] = {"is_active": False, "thread_id": str(chat_id)}

    session = user_sessions[chat_id]
    thread_id = session["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    if session["is_active"] and user_text.lower() in ['ок', 'ok', 'хорошо', 'спасибо']:
        bot.send_chat_action(chat_id, 'upload_document')

        try:
            current_state = app.get_state(config)
            artifact = current_state.values.get('draft_artifact')

            if artifact:
                md_content = render_markdown(artifact)
                filename = f"Project_{chat_id}.md"

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(md_content)

                with open(filename, "rb") as f:
                    bot.send_document(chat_id, f, caption="✅ Проект утвержден! Вот ваш итоговый файл.")

                os.remove(filename)
            else:
                bot.send_message(chat_id, "⚠️ Ошибка: Артефакт потерян. Начните заново с /start")

        except Exception as e:
            bot.send_message(chat_id, f"Ошибка при сохранении: {e}")

        session["is_active"] = False
        return

    bot.send_chat_action(chat_id, 'typing')

    try:
        if not session["is_active"]:
            bot.reply_to(message, "🚀 Принято! Анализирую идею, консультируюсь с Критиком... Это займет секунд 10-20.")

            initial_state = {
                "project_description": user_text,
                "draft_artifact": None,
                "critic_feedback": "",
                "critic_verdict": None,
                "revision_count": 0,
                "user_feedback": "",
                "user_has_provided_feedback": False,
            }
            app.invoke(initial_state, config=config)
            session["is_active"] = True

        else:
            bot.reply_to(message, f"🔄 Принято: '{user_text}'. Отправляю на доработку Аналитику...")

            app.invoke({
                "user_feedback": user_text,
                "user_has_provided_feedback": True,
                "critic_verdict": None
            }, config=config)

        current_state = app.get_state(config)
        artifact = current_state.values.get('draft_artifact')

        if artifact:
            msg_text = render_message_text(artifact)

            if len(msg_text) > 4000:
                msg_text = msg_text[:3500] + "\n\n... (Текст сокращен, полная версия будет в файле) ..."

            try:
                bot.send_message(chat_id, msg_text, parse_mode="Markdown")
            except Exception as e:
                bot.send_message(chat_id, msg_text)

            bot.send_message(chat_id,
                             "Выше текущая версия проекта ⬆️\n\n"
                             "Если все нравится — напишите **'ОК'**, и я пришлю файл.\n"
                             "Если нужны правки — напишите, что изменить.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ Что-то пошло не так, артефакт пустой. Попробуйте еще раз /start")

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"Произошла ошибка: {e}")


print("Бот запущен!")
bot.infinity_polling()