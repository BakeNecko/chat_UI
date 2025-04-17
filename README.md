# RealTime Чат-приложение 
В качестве основы выбран template-проект из офф. документации [FastAPI](https://github.com/fastapi/full-stack-fastapi-template). Больше информации -> `OLD_README.md`

Здесь уже подключен Docker и по сути почти все настроено, но я не считаю что плохо, т.к поднятие 3х сервисов в Compose и связывание их через .env, вряд ли покажет мое "Уверенное" знанание Docker'a.

## Запуск
- OS: Ubuntu 24.04.2 LTS
- Docker Compose version v2.34.0
- Docker version 28.0.4, build b8034c0

Запуск: `docker compose up --build` по желанию можно добавить `-d` для фонового режима.

`http://localhost:5173/login` - Адрес приложения. Регистрация также работает. 

Доступные пользователи 
EMAIL:    | `first@mail.ru` | `second@mail.ru` | `third@mail.ru`  | `admin@mail.ru`  |
----------|-----------------|------------------|------------------|------------------|
PASSWORD: | `qwerty123`     | `qwerty123`      | `qwerty123`      | `qwerty123`      |

## Технологии
- FastAPI
- PostgreSQL
- Docker/Docker-Compose
- React (+Chakra UI)
- Redis (PubSub)

## Архитектура
Весь **RealTime** строится на **PubSub Redis**. Изначально планировался **Kafka** и он бы и был, будь это боевой проект. 

Redis PubSub - работает по принципу отправил/забыл. Ничего не хранит, если никто не получил сообщение возвращает 0 и удаляет (теряет) сообщение.

### Base Flow (Backend):
- Клиент логинится 
- Попытка установить сокет. Если да -> идем дальше, Нет ->  ретрай через 5сек
- Инциализируем Сокет. Отправляем init сообщение с access_token, чтобы сообщий о своем пользователи и авторизоваться.
- После успешного подтверждения токена, получаем пользователя и все его чаты. Подписываемся на UUID чатов, как на имя канала. И подписываемся на личный канал пользователя, куда ему будут приходить личные собщения. Создавать отдельную подписку на каждый ЛК было бы затратно, особенно с точки зрения Kafka.
- После инициализации, запускается корутина (`receive_messages`), которая крутится в While цикле. Её задача отправлять полученные по PubSub подписке сообщения в асинк очередь.
- Задача другой корутины (end_messages) доставать сообщения из очереди и отправлять их на клиент 
- Основной While True цикл занимается отправкой и созданием сообщений клиента.


### Base Flow (Front):
- Клиент логинится 
- Инициализируем токен. Отправлям Init сообщение с JWT. Да -> Идем дальше. Нет -> retry 5 sec.
- Если читаем чат а.к запрашиваем `history/{chat_id}` то бэк помечает все сообщения как прочитанные этим пользователем. И отправляет атвору сообщения PubSub уведомление о том, что сообщение было кем-то прочитанно.
- Когда приходит сообщение с WS и мы в чате с этим сообщением, отправляется точечный запрос, чтобы пометить то сообщение как прочитанное.  
- Далее стандартная раота с ВебСокетом. На каждое сообщение генерируется UUID которое сохраняется в бд вместе с сообщением. Для предотвращения дублирования. 


### Структура Проекта
Базово у проекта была хорошая структура. 
За исключением файлов **crud.py** и **models.py**. 

**crud.py** - необходимо было превратить в папку т.к это слой работы с БД.

**models.py** - Содержал в себе как таблицы, так и просто SQLModel классы, которые использовались то тут то там как валидаторы. Поэтому это тоже правратилось в папку, а все модели не связанные с созданием БД (*DDL*) были вынесены в слой **DTO** (Data Transfer Object)

Основной код на беке который написал я:
- `api/`
  - `routes/`
    - `groups.py`
    - `msg.py`
    - `ws_chats.py`
  - `crud/`
    - `*.py`

Основной код, который я написал на фронте, прости господи:
- `ws_chat_ctx.tsx` - Провайдер-контекст вебсокета. Открывается один на все приложение. Пытается переподключаться если отвалился.
- `Chat.tsx`/`ChatsList.tsx` - Компонененты чата, через callback'и подписываются на сообщения из Сокета.
P.S 
*Вынужден признать, что мне не удалось добиться устойчивости на фронте. По этой причине например есть кнопка "Обновить чат"*
