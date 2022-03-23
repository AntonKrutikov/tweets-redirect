import asyncio
import discord
import json
import sqlite3
import tweepy
import tweepy.asynchronous
from typing import List, Union
from aiogram import Bot, Dispatcher
from datetime import datetime

LOG_NEWS = True

class Publisher():
    def add_discord(self, discord_client:discord.Client, channels:List[int]):
        self.discord_client = discord_client
        self.discord_channels = channels

    def add_telegram(self, telergam_bot:Bot, channels:List[Union[str,int]]):
        self.telegram_bot = telegram_bot
        self.telegram_channels = channels

    async def publish_discord(self, data):
        if self.discord_client and self.discord_client.is_ready():
            for channel in self.discord_channels:
                await self.discord_client.get_channel(channel).send(data)

    async def publish_telegram(self, data):
        if self.telegram_bot:
            for channel in self.telegram_channels:
                await self.telegram_bot.send_message(channel, data)

    async def publish(self, data):
        await self.publish_discord(data)
        await self.publish_telegram(data)

class TwitterClient(tweepy.asynchronous.AsyncStream):

    def add_publisher(self, publisher:Publisher):
        self.publisher = publisher

    async def on_connect(self):
        print("TwitterStream connected")

    async def on_status(self, status):
        # Also we can collect representation based on text, embedded img, filter retweets and so
        tweet_url = "https://twitter.com/twitter/statuses/%d" % status.id

        if LOG_NEWS:
            print("\n%s" % tweet_url)
            print(status.text)

        await self.publisher.publish(tweet_url)

    def names_to_id(self, targets:List[Union[int,str]]) -> List[int]:
        """Convert List of twitter @screenname to user_id. Because stream api accept only ids"""
        api = tweepy.API(tweepy.OAuth1UserHandler(self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret))
        ids = []
        for target in targets:
            if isinstance(target, int):
                ids.append(target)
            if isinstance(target, str):
                user:tweepy.User = api.get_user(screen_name = target)
                if user:
                    ids.append(user.id)
        return ids
                
    async def watch(self, targets:List[int]):
        await self.filter(follow=targets)

class SqliteClient:
    def __init__(self, dbname):
        self.connection = sqlite3.connect(dbname)
        print('SqliteClient connected')

    def add_publisher(self, publisher:Publisher):
        self.publisher = publisher

    async def watch(self, delay=15):
        cursor = self.connection.cursor()
        update_cursor = self.connection.cursor()
        while True:
            for row in cursor.execute('SELECT id, text FROM nft_news WHERE publish=1 and published_date is NULL'):
                if LOG_NEWS:
                    print("\nFrom sqlite storage:")
                    print(row[1])
                await self.publisher.publish(row[1])
                published_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                update_cursor.execute('UPDATE nft_news SET published_date=? WHERE id=?', (published_date,row[0]) )
                self.connection.commit()
            await asyncio.sleep(delay)

conf = open("./config.json")
config = json.load(conf)

# Telegram
telegram_bot = Bot(token=config["telegram"]["token"])
telegram_dispatcher = Dispatcher(telegram_bot)
async def telegram_bot_run():
    user = await telegram_dispatcher.bot.me
    print("TelegramBot connected (%s, [@%s])" % (user.full_name, user.username))
    await telegram_dispatcher.start_polling()

# Discord
discord_client = discord.Client()
@discord_client.event
async def on_ready():
    print("DiscordClient connected")

# Publisher
publisher = Publisher()
publisher.add_discord(discord_client=discord_client, channels=config["discord"]["channels"])
publisher.add_telegram(telergam_bot=telegram_bot, channels=config["telegram"]["channels"])

# Twitter
twitter_client = TwitterClient(
    config["twitter"]["consumer_key"], 
    config["twitter"]["consumer_secret"], 
    config["twitter"]["access_token"], 
    config["twitter"]["access_token_secret"]
)
twitter_targets = twitter_client.names_to_id(config["twitter"]["targets"])
twitter_client.add_publisher(publisher)

# Sqlite
sqlite_client = SqliteClient(config["sqlite_db"])
sqlite_client.add_publisher(publisher)

# Event loop
loop = asyncio.get_event_loop_policy().get_event_loop()
loop.create_task(discord_client.start(config["discord"]["token"]))
loop.create_task(telegram_bot_run())
loop.create_task(twitter_client.watch(twitter_targets))
loop.create_task(sqlite_client.watch())
loop.run_forever()
