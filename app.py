import asyncio
import discord
import json
import tweepy.asynchronous
from typing import List, Union
from aiogram import Bot, Dispatcher

LOG_TWEETS = True

class TwitterClient(tweepy.asynchronous.AsyncStream):

    def add_discord(self, discord_client:discord.Client, channels:List[int]):
        self.discord_client = discord_client
        self.discord_channels = channels

    def add_telegram(self, telergam_bot:Bot, channels:List[Union[str,int]]):
        self.telegram_bot = telegram_bot
        self.telegram_channels = channels

    async def on_connect(self):
        print("TwitterStream connected")

    async def on_status(self, status):
        # Also we can collect representation based on text, embedded img, filter retweets and so
        tweet_url = "https://twitter.com/twitter/statuses/%d" % status.id

        if LOG_TWEETS:
            print("\n%s" % tweet_url)
            print(status.text)

        if self.discord_client and self.discord_client.is_ready():
            for channel in self.discord_channels:
                await self.discord_client.get_channel(channel).send(tweet_url)

        for channel in self.telegram_channels:
            await self.telegram_bot.send_message(channel, tweet_url)

    async def watch(self, ids:List[int]):
        await self.filter(follow=ids)


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

# Twitter
twitter_client = TwitterClient(
    config["twitter"]["consumer_key"], 
    config["twitter"]["consumer_secret"], 
    config["twitter"]["access_token"], 
    config["twitter"]["access_token_secret"]
)
twitter_client.add_discord(discord_client=discord_client, channels=config["discord"]["channels"])
twitter_client.add_telegram(telergam_bot=telegram_bot, channels=config["telegram"]["channels"])

# Event loop
loop = asyncio.get_event_loop_policy().get_event_loop()
loop.create_task(discord_client.start(config["discord"]["token"]))
loop.create_task(telegram_bot_run())
loop.create_task(twitter_client.watch(config["twitter"]["targets"]))
loop.run_forever()