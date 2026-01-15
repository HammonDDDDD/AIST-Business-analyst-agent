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
    """
    Generate complete Markdown documentation for project artifacts.
    
    This method creates structured documentation by extracting key project information
    from artifact dictionaries and formatting it into a comprehensive Markdown document.
    The generated documentation serves as a complete reference that captures project
    goals, requirements, and descriptions in a standardized format suitable for
    preservation and sharing.
    
    Args:
        artifact (dict): A dictionary containing project artifact data with keys such
                        as 'title', 'description', 'goals', and 'functional_requirements'.
                        The dictionary should contain the necessary project metadata
                        to generate meaningful documentation.
    
    Returns:
        str: A formatted Markdown string containing the complete project documentation.
             Returns "Нет данных" if the input artifact is empty or None.
    """
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
    """
    Генерация текста для сообщения в Telegram с упрощенным форматированием.
    
    Форматирует данные проекта в читаемый текст для отправки в мессенджер, 
    структурируя информацию по ключевым разделам для удобного восприятия.
    
    Args:
        artifact (dict): Словарь с данными проекта, содержащий информацию о названии,
            описании, целях и функциональных требованиях.
    
    Returns:
        str: Отформатированное текстовое сообщение с разделами проекта, готовое для отправки.
            В случае отсутствия данных возвращает сообщение об ошибке.
    
    Why:
        Метод преобразует структурированные данные проекта в удобочитаемый формат для 
        быстрого ознакомления пользователей с ключевой информацией через мессенджер.
    """
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
    """
    Sends a welcome message and initializes a user session when the /start command is received.
    
    WHY: This method establishes a new conversation context for each user, allowing the system to maintain state across multiple interactions and provide personalized assistance throughout the project development cycle.
    
    Args:
        message: The incoming message object containing chat details.
    
    Initializes:
        user_sessions[chat_id] (dict): A session dictionary for the user with keys:
            - is_active (bool): Indicates if the user session is currently active
            - thread_id (str): Unique identifier for the user's conversation thread
    
    Returns:
        None
    """
    chat_id = message.chat.id
    user_sessions[chat_id] = {"is_active": False, "thread_id": str(chat_id)}

    bot.reply_to(message,
                 "👋 Привет! Я AI-Бизнес-аналитик.\n\n"
                 "Напиши мне идею своего проекта (например: 'Хочу сервис доставки еды дронами'), "
                 "и я подготовлю ТЗ с функциональными требованиями.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """
    Handles incoming user messages to manage iterative project feedback cycles for project development.
    
    This method serves as the core interaction handler for a collaborative project refinement process. It maintains session state to track project evolution through multiple revision cycles, allowing users to provide feedback and receive updated project artifacts until final approval.
    
    The method enables iterative refinement by:
    - Starting new project cycles when users submit initial descriptions
    - Processing user feedback to trigger successive revisions
    - Managing approval flow when users accept the final version
    - Maintaining session continuity throughout the feedback loop
    
    Args:
        message: The incoming message object containing chat information and user input text
    
    Returns:
        None: Responses are sent directly via the bot interface rather than returning values
    """
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