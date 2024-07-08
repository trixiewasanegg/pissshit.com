import logging
import discord
from dotenv import load_dotenv
import os
import pytz

# Loads environment file
load_dotenv()
token = os.getenv('TOKEN')
pathDelim = os.getenv('PATHDELIM')
microChannelID = int(os.getenv('CHANNEL'))
microMD = str(os.getenv('MDPATH')) + pathDelim + "microMessages.md"

handler = logging.FileHandler(filename='DiscordBot.log', encoding='utf-8', mode='w')

async def messageUpdate(self):
	channel = self.get_channel(microChannelID,)
	markdownLines = []
	async for message in channel.history(limit=100):
		# Gets datetime datestamp of message, converts to datestamp:\
		date = message.created_at
		date = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Australia/Perth'))
		datestamp = date.strftime("%d %b %Y, %I:%M %p") + " AWST"
		
		# Gets message author, avatar, message content, and embeds
		author = message.author.display_name
		avatar = message.author.avatar.url
		content = message.clean_content
		embed = message.embeds

		# Checks if reply, gets replied message details
		if message.type == discord.MessageType.reply:
			replyMsg = message.reference.resolved
			replyTo = replyMsg.author.display_name
			replyContent = replyMsg.clean_content
			content = content + "<br />\n<br />\n_Original Message:_<br />\n> " + replyContent
			context = "\n_replied to " + replyTo + " at " + datestamp + "_<br />"
		else:
			context = "\n_wrote at " + datestamp + "_<br />"

		markdownLines.append("### " + author + "\n")
		markdownLines.append(context)
		markdownLines.append(content + "\n")
		markdownLines.append("---")
	file = open(microMD,"w")
	for lin in markdownLines:
		file.write(lin + "\n")
	file.close()
	print("Messages Updated")	

class MyClient(discord.Client):
	async def on_ready(self):
		print(f'Logged on as {self.user}!')
		await messageUpdate(self)		

	# When message sent, 
	async def on_message(self, msg):
		await messageUpdate(self)		
	
	async def on_raw_message_delete(self, msg):
		await messageUpdate(self)		


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token, log_handler=handler)