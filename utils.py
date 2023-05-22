from ast import alias
import discord
from discord.ext import commands
from youtube_dl import YoutubeDL
import os
import openai
import urllib.request
from math import factorial



class Expandor:
	def __init__(self,expr):
		self.expr = "".join([i for i in expr if i!=" "])


	def expand(self):
		expr = self.expr
		print(self.expr)
		expr = expr.replace("(", "").replace(")", "")
		calc = Calculator(expr)

		n = calc.getN()
		if n == 0: return '1'

		a, b = calc.getA_B()
		x = calc.getX(a)
		b = int(b)
		try:
			a = int(a[:len(a) - 1])

		except ValueError:
			a = 1 if a[0] != "-" else -1

		coeffs = calc.binomialTherom(a, b, n)
		coeffs_parsed = [f'{coeffs[i]}{x}^{n - i}' if i != len(coeffs) - 1 else f'{coeffs[i]}' for i in
		                 range(0, len(coeffs))]
		validated_coeffs = calc.__validate_coeffs__(coeffs_parsed, x)
		result = calc.__remove__uwanted_exponent__(validated_coeffs)
		return "".join([f'+{i}' if i[0] != "-" and result.index(i) != 0 else i for i in result])


class Calculator:
	def __init__(self, expression):
		self.expression = expression

	def getN(self):
		n = [i for i in self.expression]

		self.expression = "".join(self.expression.split("^")[0])
		print(self.expression)
		return int("".join(n[n.index('^') + 1:len(n)]))



	def getX(self, a):
		return a[-1]

	@staticmethod
	def strip_white_space(a, b):
		return "".join([i for i in a if i != " "]).strip(), "".join([i for i in b if i != " "]).strip()

	def getA_B(self):

		expr = self.expression

		option1 = False
		if expr.count("-") == 1 or expr.count("-") == 0:
			option1 = True

		if option1:
			operators = ["+", "-"]

			try:
				a, b = expr.split("+")

			except ValueError:
				expr = expr.replace("-", " -")
				a, b = expr.split(" ")

			return self.strip_white_space(a, b)[0], self.strip_white_space(a, b)[1]

		else:
			operators = ["-", "-"]
			indx = []
			for i in range(0, len(expr)):
				if expr[i] == "-":
					indx.append(i)

			a, b = expr[0:indx[-1]], expr[indx[-1]: len(expr)]
			return self.strip_white_space(a, b)[0], self.strip_white_space(a, b)[1]

	def binomialTherom(self, a, b, n):
		k = 0
		coeffs = []
		for i in range(n + 1):
			comb_custom = lambda nn, kk: factorial(nn) / (factorial(kk) * (factorial(nn - kk)))
			coeffs.append(int(comb_custom(n, k) * (a ** (n - k)) * (b ** k)))
			k += 1

		return coeffs

	def __validate_coeffs__(self, parsed_coeffs, x):
		result = []
		for i in parsed_coeffs:
			# find index of x
			if i.count(x) != 0:
				if i[:i.index(x)] == '1':

					i = f'{i[1:]}'

					result.append(i)

				elif i[:i.index(x)] == "-1":

					i = f'-{i[2:]}'

					result.append(i)


				else:
					result.append(i)
			else:
				result.append(i)

		return result

	def __remove__uwanted_exponent__(self, parsed_coeffs):
		for each in parsed_coeffs:
			try:
				if each[each.index("^") + 1:len(each)] == "1":
					parsed_coeffs[parsed_coeffs.index(each)] = each.split("^")[0]

			except ValueError:
				pass

		return parsed_coeffs



class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.help_message = "\n".join([
	        "Allmänna kommandon:\n\n","$help - visar alla tillgängliga kommandon",
            "$spela <låt namn> - hittar låten på youtube och spelar den i din nuvarande kanal. Kommer att återuppta uppspelningen av den aktuella låten om den var pausad",
	        "$kö - visar den aktuella musikkön",
	        "$skippa - hoppar över den aktuella låten som spelas",
	        "$töm - Stoppar musiken och rensar kön",
	        "$lämna - Kopplade bort boten från röstkanalen",
	        "$pausa - pausar den aktuella låten som spelas eller återupptas om den redan är pausad",
	        "$återuppta - återupptar uppspelningen av den aktuella låten",
	        "$gen - genererar bild med hjälp av en beskrivning",
	        "$binom - utvecklar binomiala uttryck (Indata måste följa formatet : (ax+-b)^n | där b är en konstant",
        ])



        self.text_channel_list = []

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                self.text_channel_list.append(channel)

        await self.send_to_all(self.help_message)

    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send(f"```\n{self.help_message}\n```")

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_list:
            await text_channel.send(f"```\n{self.help_message}\n```")



class music_cog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.is_playing = False
		self.is_paused = False

		self.music_queue = []
		self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
		self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}
		self.vc = None

	def search_yt(self, item):
		with YoutubeDL(self.YDL_OPTIONS) as ydl:
			try:
				info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
			except Exception:
				return False

		return {'source': info['formats'][0]['url'], 'title': info['title']}

	def play_next(self):
		if len(self.music_queue):
			self.is_playing = True

			m_url = self.music_queue[0][0]['source']

			self.music_queue.pop(0)

			self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
		else:
			self.is_playing = False

	async def play_music(self, ctx):
		if len(self.music_queue) > 0:
			self.is_playing = True

			m_url = self.music_queue[0][0]['source']

			if not self.vc or not self.vc.is_connected():
				self.vc = await self.music_queue[0][1].connect()

				if not self.vc:
					await ctx.send("Det gick inte att ansluta till röstkanalen")
					return
			else:
				await self.vc.move_to(self.music_queue[0][1])

			self.music_queue.pop(0)

			self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
		else:
			self.is_playing = False

	@commands.command(name="spela")
	async def play(self, ctx, *args):
		query = " ".join(args)

		voice_channel = ctx.author.voice.channel
		if not voice_channel:
			await ctx.send("Anslut till en röstkanal!")
		elif self.is_paused:
			self.vc.resume()
		else:
			song = self.search_yt(query)
			if isinstance(song,bool):
				await ctx.send(
					"Kunde inte ladda ner låten.")
			else:
				await ctx.send("Låten har lagts till i kön")
				self.music_queue.append([song, voice_channel])

				if not self.is_playing:
					await self.play_music(ctx)

	@commands.command(name="pausa")
	async def pause(self, ctx, *args):
		if self.is_playing:
			self.is_playing = False
			self.is_paused = True
			self.vc.pause()
		elif self.is_paused:
			self.is_paused = False
			self.is_playing = True
			self.vc.resume()

	@commands.command(name="återuppta")
	async def resume(self, ctx, *args):
		if self.is_paused:
			self.is_paused = False
			self.is_playing = True
			self.vc.resume()

	@commands.command(name="skippa")
	async def skip(self, ctx):
		if self.vc:
			self.vc.stop()
			await self.play_music(ctx)

	@commands.command(name="kö")
	async def queue(self, ctx):
		retval = ""
		for i in range(0, len(self.music_queue)):
			if (i > 4): break
			retval += self.music_queue[i][0]['title'] + "\n"

		if retval != "":
			await ctx.send(retval)
		else:
			await ctx.send("Ingen musik i kö")

	@commands.command(name="töm")
	async def clear(self, ctx):
		if self.vc != None and self.is_playing:
			self.vc.stop()
		self.music_queue = []
		await ctx.send("Musikkön har rensats")

	@commands.command(name="lämna")
	async def dc(self, ctx):
		self.is_playing = False
		self.is_paused = False
		await self.vc.disconnect()


class Backend:
    def __init__(self, prompt:str) -> None:
        self.prompt = prompt

    def generateImg(self) -> str:
        openai.api_key = "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"
        response = openai.Image.create(
        prompt=self.prompt,
        n=1,
        size="1024x1024"
        )

        image_url = response['data'][0]['url']
        return image_url


