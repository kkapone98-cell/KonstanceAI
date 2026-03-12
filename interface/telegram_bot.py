from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import json, pathlib
from core.planner import plan_task
from agents import coding_agent, research_agent, automation_agent, chat_agent

MEM_CONV = pathlib.Path(r'C:\Users\Thinkpad\Desktop\KonstanceAI\memory\conversations.json')
MEM_CONV.parent.mkdir(parents=True, exist_ok=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text
    if MEM_CONV.exists():
        data = json.load(open(MEM_CONV,'r',encoding='utf-8'))
    else:
        data = []
    task = plan_task(txt)
    tp = task.get('task_type')
    if tp == 'coding':
        out = coding_agent.run_task(task)
    elif tp == 'research':
        out = research_agent.run_task(task)
    elif tp == 'automation':
        out = automation_agent.run_task(task)
    else:
        out = chat_agent.run_task(task)
    data.append({'user': txt,'ai': out})
    json.dump(data, open(MEM_CONV,'w',encoding='utf-8'), indent=2)
    await update.message.reply_text(out)

def run_bot(base_dir):
    app = ApplicationBuilder().token('8727908300:AAGmENqjdiqVi3gxInPQDIEdqPFcme8-iL4').build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
