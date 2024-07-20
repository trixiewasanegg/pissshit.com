import logging
import discord
from dotenv import load_dotenv
import os
import shutil
import pytz

# Loads environment file
load_dotenv()
token = os.getenv('TOKEN')
pathDelim = os.getenv('PATHDELIM')

#Channel Config
microChannelID = int(os.getenv('MICROCHANNEL'))
microMD = str(os.getenv('MDPATH')) + pathDelim + "microMessages.md"
blogChannelID = int(os.getenv('BLOGCHANNEL'))
blogMD = str(os.getenv('MDPATH')) + pathDelim + "blogMessages.md"
postsDir = str(os.getenv('POSTDIR'))
aboutChannelID = int(os.getenv('ABOUTCHANNEL'))
aboutMD = str(os.getenv('MDPATH')) + pathDelim + "about.md"
logChannelID = int(os.getenv('LOGCHANNEL'))

# Three Channel Types:
# MB - Microblogging
# BL - Blogging
# AB - About
channels = [(microChannelID,microMD,'MB'), (blogChannelID,blogMD,'BL'), (aboutChannelID,aboutMD,'AB')]
ignoredChannels = [logChannelID]

handler = logging.FileHandler(filename='DiscordBot.log', encoding='utf-8', mode='w')

async def logToChannel(self, trigger, text):
	logChannel = self.get_channel(logChannelID,)
	guildID = str(trigger.guild.id)
	channelID = str(trigger.channel.id)
	messageID = str(trigger.id)
	author = str(trigger.author.id)
	message = f"Re: https://discord.com/channels/{guildID}/{channelID}/{messageID}\n <@{author}> - This message has returned an error:\n{str(text)}"
	await logChannel.send(message)

async def messageUpdate(self):
	for channel in channels:
		channelData = self.get_channel(channel[0],)
		markdownLines = []

		# Adds a bit of boilerplate for the about me update
		if channel[2] == "AB":
			markdownLines.append(f"# Current contributors of {channelData.guild.name}")
			markdownLines.append("<br />")
			markdownLines.append('<table style="width:100%">')
		elif channel[2] == "BL":
			slugs = []
		async for message in channelData.history(limit=100):
			# Gets datetime datestamp of message, converts to datestamp:
			date = message.created_at
			date = date.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Australia/Perth'))
			datestamp = date.strftime("%d %b %Y, %I:%M %p") + " AWST"
			
			# Gets message author, avatar, message content, and embeds
			author = message.author.display_name
			avatar = message.author.avatar.url
			content = message.clean_content
			attached = message.attachments
			embeds = message.embeds
			# Checks channel type & splits off from there
			if channel[2] == "MB":
				# Checks if reply, gets replied message details
				if message.type == discord.MessageType.reply:
					replyMsg = message.reference.resolved
					replyTo = replyMsg.author.display_name
					replyContent = replyMsg.clean_content
					content = content + "<br />\n<br />\n_Original Message:_<br />\n> " + replyContent
					context = "\n_replied to " + replyTo + " at " + datestamp + "_<br />"
				else:
					context = "\n_wrote at " + datestamp + "_<br />"

				# Appends markdown file with the content & context
				markdownLines.append("### " + author + "\n")
				markdownLines.append(context)
				markdownLines.append(content + "\n")
				for attachment in attached:
					if attachment.content_type.split("/")[0] == "image":
						markdownLines.append(f'<img src="{attachment.url}"><br />')
					if attachment.content_type.split("/")[0] == "video":
						markdownLines.append(f'<video controls> <source src="{attachment.url}" type={attachment.content_type}> Your browser does not support the video tag. </video><br />')
				for embed in embeds:
					if embed.type == "video" or embed.type == "gifv":
						markdownLines.append(f'<video controls> <source src="{embed.url}"> Your browser does not support the video tag. </video><br />')
				markdownLines.append("---")

			# Builds tables for about section
			elif channel[2] == "AB":
				markdownLines.append("<tr>")
				markdownLines.append(f'<td style="width:30%"><img src="{avatar}" max-width="400" alt="{author}display image"></td>')
				markdownLines.append(f'<td style="width:70%"><h3>{author}</h3><br />{content}</td>')
				markdownLines.append("</tr>")

			elif channel[2] == "BL":
				key = []
				value = []
				for line in content.split("\n"):
					pair = line.split(": ")
					key.append(pair[0])
					value.append(pair[1])
				try:
					title = value[key.index("Title")]
					slug = value[key.index("Slug")]
					publishDate = value[key.index("Published")]
				except:
					await logToChannel(self, message, "Key not found. Ensure message includes Title, Slug, and Published separated by ': ' only.")
				
				path = f'{postsDir}{pathDelim}{slug}'
				if not os.path.exists(path):
					os.makedirs(path)

				for attachment in attached:
					if attachment.content_type.split("/")[0] != "text":
						await logToChannel(self, message, "Invalid attachment for blog - must be text")
					if attachment.content_type.split("; ")[0].split("/")[1] != "markdown":
						print("non-markdown")
		# Adds a bit of boilerplate for the about update
		if channel[2] == "AB":
			markdownLines.append("</table>")
		
		# Opens the file, writes the markdown
		file = open(channel[1],"w")
		for lin in markdownLines:
			file.write(lin + "\n")
		file.close()
	print("Messages Updated")

class MyClient(discord.Client):
	async def on_ready(self):
		print(f'Logged on as {self.user}!')
		print(f"Bot ID {self.user.id}")
		await messageUpdate(self)		

	# When message sent, 
	async def on_message(self, msg):
		if msg.author.id != self.user.id:
			await messageUpdate(self)		
	
	async def on_raw_message_delete(self, msg):
		await messageUpdate(self)

	async def on_member_update(self,before,after):
		await messageUpdate(self)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = MyClient(intents=intents)
client.run(token, log_handler=handler)