# bot_fish
fish store bot
## start
Create `virtualenv`
```bash
virtualenv -p 3.9 ENV_NAME
```
Activate virtualenv
```bash
source ./ENV_NAME/bin/activate
```
Copy `example.env` and write you tokens
```bash
cp example.env .env
```
```
STRAPI_TOKEN=......970e46d72c53085063c57abd894edf4...4705054b7
TM_BOT_TOKEN=67785...MMJ6sqVynaTGIa0
REDIS_HOST='localhost'
REDIS_PORT=6379
```
Run Redis server
```bash
redis-server
```
Go to project catalog
```bash
cd ./fish-store-bot/
```
Run Strapi
```bash
npm run develop
```
Run bot from root catalogue of project
```bash
python bot_fish.py
```
