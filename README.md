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
