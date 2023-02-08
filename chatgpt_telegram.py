

# 1. Начните с импорта необходимых библиотек и настройки клиентов API 
import requests
import json
import os
import threading

# OpenAI секретный ключ
API_KEY = 'xxxxxxxxxxxsecretAPIxxxxxxxxxx'
# Models: text-davinci-003,text-curie-001,text-babbage-001,text-ada-001
MODEL = 'text-davinci-003'

# Telegram токен бота
BOT_TOKEN = 'xxxxxxbotapikeyxxxxx'
# определяем характер телеграм бота
BOT_PERSONALITY = 'Answer in a funny tone, '

# 2a. получаем ответ от OpenAI
def openAI(prompt):
    # запрос на OpenAI API
    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'model': MODEL, 'prompt': prompt, 'temperature': 0.4, 'max_tokens': 300}
    )

    result = response.json()
    final_result = ''.join(choice['text'] for choice in result['choices'])
    return final_result

# 2b. функци получения изображения от OpenAI
def openAImage(prompt):
    # запрос на  OpenAI API
    resp = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers={'Authorization': f'Bearer {API_KEY}'},
        json={'prompt': prompt,'n' : 1, 'size': '1024x1024'}
    )
    response_text = json.loads(resp.text)
      
    return response_text['data'][0]['url']
  
# 3a. функция отправки сообщения в группу
def telegram_bot_sendtext(bot_message,chat_id,msg_id):
    data = {
        'chat_id': chat_id,
        'text': bot_message,
        'reply_to_message_id': msg_id
    }
    response = requests.post(
        'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage',
        json=data
    )
    return response.json()

# 3b. функция отправки картинки в группу
def telegram_bot_sendimage(image_url, group_id, msg_id):
    data = {
        'chat_id': group_id, 
        'photo': image_url,
        'reply_to_message_id': msg_id
    }
    url = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendPhoto'
    
    response = requests.post(url, data=data)
    return response.json()
  
# 4. Функция получения последних запросов от пользователей в группе Telegram,
# генерирует ответ, используя OpenAI, и отправляет ответ обратно в группу.
def Chatbot():
# Получить последнее сообщение ID из текстового файла для обновления ChatGPT
    cwd = os.getcwd()
    filename = cwd + '/chatgpt.txt'
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("1")
    else:
        print("File Exists")    

    with open(filename) as f:
        last_update = f.read()
        
# Проверить наличие новых сообщений в группе Telegram
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update}'
    response = requests.get(url)
    data = json.loads(response.content)
        
    for result in data['result']:
        try:
       # Проверка нового сообщения
            if float(result['update_id']) > float(last_update):
                 # Проверка новых сообщений, пришедших не из chatGPT
                if not result['message']['from']['is_bot']:
                    last_update = str(int(result['update_id']))
                    
                  # Получение идентификатора сообщения отправителя запроса
                    msg_id = str(int(result['message']['message_id']))
                    
                    # получаем ID 
                    chat_id = str(result['message']['chat']['id'])
                    
                    # проверка нужна ли картинка пользователю
                    if '/img' in result['message']['text']:
                        prompt = result['message']['text'].replace("/img", "")
                        bot_response = openAImage(prompt)
                        print(telegram_bot_sendimage(bot_response, chat_id, msg_id))
                    # Проверка того, что пользователь упомянул имя пользователя чат-бота в сообщении
                    if '@ask_chatgptbot' in result['message']['text']:
                        prompt = result['message']['text'].replace("@ask_chatgptbot", "")
                      # Вызов OpenAI API с использованием личности бота
                        bot_response = openAI(f"{BOT_PERSONALITY}{prompt}")
                      # Отправляем ответ группе телеграмм
                        print(telegram_bot_sendtext(bot_response, chat_id, msg_id))
             # Проверка того, что пользователь отвечает боту ChatGPT
                    if 'reply_to_message' in result['message']:
                        if result['message']['reply_to_message']['from']['is_bot']:
                            prompt = result['message']['text']
                            bot_response = openAI(f"{BOT_PERSONALITY}{prompt}")
                            print(telegram_bot_sendtext(bot_response, chat_id, msg_id))
        except Exception as e: 
            print(e)

    # в файл сохраняем последний id
    with open(filename, 'w') as f:
        f.write(last_update)
    
    return "done"

# 5 Запускаем проверку каждые 5 секунд на наличие новых сообщений
def main():
    timertime=5
    Chatbot()   
    # 5 sec timer
    threading.Timer(timertime, main).start()

# запускаем main
if __name__ == "__main__":
    main()
    