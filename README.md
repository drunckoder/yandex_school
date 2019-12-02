# yandex_school

# **Инструкция по установке**:  

`sudo apt update && sudo apt upgrade -y` - обновляем пакеты  
`sudo reboot` - перезагрузим сервер, если увидим сообщение о надобности перезагрузки  
`sudo apt install postgres postgresql-server-dev-10 nginx python3-pip python3-venv supervisor git` - установка  
необходимых для приложения пакетов.  

# Настройка Postgres

`sudo nano /etc/postgresql/10/main/pg_hba.conf` - поменяем правила доступа к Postgres  

Нам могут понадобится эти правила:

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             all                                     trust  # свободный доступ в localhost
# IPv4 local connections:
host    all             entrant         0.0.0.0/0               md5   # если нужен доступ к БД извне, можно не добавлять

```

`CTRL+X -> y` - сохраняем, выходим  

`sudo nano /etc/postgresql/10/main/postgresql.conf` - если нужен доступ к БД извне   

Меняем строки в файле так, чтобы они приняли вид:  

```
listen_addresses = '*'                  # какие адреса слушаем. * - все адреса (снизит безопасность сервера!).
                                        # можно указать нужные адреса.
```
```
port = 5432 # порт по умолчанию
```  
  
`CTRL+X -> y` - сохраняем, выходим 

`sudo systemctl restart postgresql` - перезапустим Postgres

Создадим роли БД:  

```
sudo su postgres
psql
```

Как вошли в клиент psql, пишем:

```
ALTER USER postgres WITH PASSWORD '$password';  

CREATE USER entrant NOSUPERUSER;
ALTER USER entrant WITH PASSWORD '$entrant_password';  
ALTER USER entrant createdb;

\q - выход из клиента
```
  
Создадим БД для нашего пользователя  

`createdb entrant`  
  
`CTRL+D`  - выходим из пользователя postgres  

Создадим БД для приложения:  
  
`createdb yandex_school` - для работы самого приложения  
`createdb yandex_school_test` - для тестирования  

# Настройка nginx  

Создаем файл

`sudo nano /etc/nginx/sites-enabled/yandex_school`  

с содержимым:  

```
server {
        # внешний порт приложения
        listen 8080; 
        # адреса, которые нужно "маршрутизировать"
        location / {
                proxy_pass http://127.0.0.1:5000; # внутренний адрес:порт, на который надо перенаправлять запросы
        }
}
```

`systemctl restart nginx` - перезагрузим
`systemctl status nginx` - проверим статус, убедимся что все работает


# Деплоим код приложения  

(У вас должны быть права доступа к репозиторию. В директории ~/.ssh находится ключ доступа с паролем 0mSx0gTX8nAeTjmM)


`git clone git@github.com:drunckoder/yandex_school.git`

`cd yandex_school/`

`python3 -m venv venv` - создадим виртуальное окружение

`source venv/bin/activate` - активируем

`pip3 install wheel` - нужен для сборки wheel-ок

`pip3 install -r requirements.txt` - устанавливаем зависимости из файла

`./init_db.sh` - инициализация базы даных (важно!)

# Запуск тестов

`./test.sh`  

# Настройка Supervisord  

`sudo nano /etc/supervisor/conf.d/yandex_school.conf` - создадим файл конфигурации приложения  

Содержимое файла:

```
[program:yandex_school]
directory=~/yandex_school                             ; - рабочая директория
command=~/yandex_school/run.sh                        ; - команда запуска
autostart=true                                        ; - автозагрузка
autorestart=true                                      ; - автоперезагрузка в случае падения
stderr_logfile=~/yandex_school/yandex_school.err.log  ; - путь stderr
stdout_logfile=~/yandex_school/yandex_school.out.log  ; - путь stdout
stopsignal=KILL                                       ; - сигнал остановки
stopasgroup=true                                      ; - остановка дочерних процессов Gunicorn
```

`sudo nano /etc/supervisor/supervisord.conf` - редактируем файл, если нужен доступ к панели управления через веб-браузер

Нужно добавить в файл:

```
[inet_http_server]            ; inet (TCP) server disabled by default
port=*:9001                   ; (ip_address:port specifier, *:port for all iface)
username=drunckoder           ; (default is no username (open server))
password=hunter2              ; (default is no password (open server))
```

`sudo supervisorctl reread` - применяем настройки (важно!)

`sudo service supervisor restart` - перезапускаем сервер, чтобы стала доступна панель управления


http://<host_address>:9001/ - доступ к панели упавления
