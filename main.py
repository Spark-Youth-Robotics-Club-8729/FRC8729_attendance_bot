import discord
from discord.ext import commands
from discord import app_commands
import os
import time
import sqlite3
import datetime

import asyncio  # Added for background task

from dotenv import load_dotenv
from spreadsheet import createNewCalendar


# GETTING VALUES FROM .env
load_dotenv(".env")
# authentication token for discord bot to connect to discord
TOKEN: str = os.getenv("TOKEN")
# discord server id (to be used in GUILD_ID)
ID: int = os.getenv("ID")
# specific channel id for the channel where bot messages are sent
CHAN: int = int(os.getenv("CHAN"))


# CLASS DEFINITIONS + INITIALIZATIONS
# class to customize behavior of discord bot
class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")

        try:
            guild = discord.Object(id=ID)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")
        except Exception as e:
            print(f"Error syncing commands: {e}")

        # Start the background task
        self.loop.create_task(self.send_hello_loop())

    async def send_hello_loop(self):
        await self.wait_until_ready()  # Ensure bot is ready before running
        channel = self.get_channel(CHAN)  # Get the channel
        
        while not self.is_closed():
            now = datetime.datetime.now()
            next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)

            # If it's already past 1 AM today, schedule for tomorrow
            if now > next_run:
                next_run += datetime.timedelta(days=1)

            # Calculate the sleep duration
            sleep_time = (next_run - now).total_seconds()
            print(f"Sleeping for {sleep_time} seconds until 1 AM...")

            await asyncio.sleep(sleep_time)  # Wait until 1 AM

            if channel:
                cursor.execute(f"UPDATE team SET App = 'FALSE'")
                cursor.execute(f"UPDATE team SET Total = 0")
                database.commit()

                await channel.send("All members have been clocked out!")

            await asyncio.sleep(86400)  # Ensure it waits 24 hours after sending


# defines ui for the bot
class MyView(discord.ui.View):
    def __init__(self, timeout=86400):
        super().__init__(timeout=timeout)
        self.value = None

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.green)
    async def button_approved(self, interaction, button):
        button.disabled = True  # set button.disabled to True to disable the button
        button.label = f"Approved by {interaction.user.display_name}"  # change the button's label to something else
        await interaction.response.edit_message(view=self)  # edit the message's view
        self.value = True
        self.stop()

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def button_denied(self, interaction, button):
        button.disabled = True  # set button.disabled to True to disable the button
        button.label = f"Denied by {interaction.user.display_name}"  # change the button's label to something else
        await interaction.response.edit_message(view=self)  # edit the message's view
        self.value = False
        self.stop()


# FUNCTIONS TO HELP OUT WITH THE BOT
def checkClockedIn(user):
    # queries table to see if App is true (logged in)
    cursor.execute(f"SELECT Name, App FROM team WHERE Name = ('{user}')")
    for row in cursor.fetchall():
        if "TRUE" in str(row):
            return True
        else:
            return False


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    return "%d:%02d:%02d" % (hour, minutes, seconds)

def convertToHours(seconds):
    return seconds/3600


def divide_chunks(l, n):
    # used to divide long list of users into smaller chunks for easier processing
    for i in range(0, len(l), n):
        yield l[i : i + n]


intents = discord.Intents.default()
intents.message_content = True

client = Client(command_prefix="!", intents=intents)

# specific discord server id
GUILD_ID = discord.Object(id=ID)

database = sqlite3.connect("List.db")
cursor = database.cursor()  # database cursor to interact with the database
# table: team (software, b&o, mech)
# columns: (Name, Total, ClockIn (timestamp), App (if clocked in), Request (for clocking out), Role, Paused (for avoiding accidental clockins))
# rows: the people
database.execute(
    "CREATE TABLE IF NOT EXISTS team(Name STRING, Total INT, ClockIn INT, App STRING, Request INT, Role STRING, Paused BOOLEAN DEFAULT FALSE)"
)


# Commands for the bot
@client.tree.command(
    name="list", description="List all users (1=sw, 2=b&o, 3=mech)", guild=GUILD_ID
)
async def listUsers(interaction: discord.Interaction, team: int):
    # function to get list of all tracked members from a specific subteam
    if team == 1:
        ans = "SOFTWARE"
    elif team == 2:
        ans = "B&O"
    elif team == 3:
        ans = "MECHANICAL"
    else:
        ans = "IDK"

    # fetch users based on the role
    cursor.execute(f"SELECT Name, Total, App FROM team WHERE Role = ('{ans}')")
    people = list(cursor.fetchall())

    # if no users are found, send a "No users" message
    if not people:
        await interaction.response.send_message("No saved members.")
        return

    # proceed with creating and sending embeds if users are found
    embeds = []
    chunks = list(divide_chunks(people, 25))
    for chunk in chunks:
        embed = discord.Embed(
            title="List of Users",
            description=f"Here is the list of all members from {ans}!",
            color=discord.Color.random(),
            timestamp=datetime.datetime.now(),
        )
        for row in chunk:
            embed.add_field(
                name=row[0],
                value=f"Total Time (HH:MM:SS): {convert(row[1])}\nCurrently Clocked In: {'No' if row[2] == 'FALSE' else 'Yes'}",
                inline=False,
            )
        embeds.append(embed)

    await interaction.response.send_message(embeds=embeds)


@client.tree.command(
    name="clockin", description="Clock in (start your timer)", guild=GUILD_ID
)
async def clockIn(interaction: discord.Interaction):
    # function to clock in users

    # variable to track if user has existing record in database
    app = False

    # try querying the database for the user + if they're clocked in
    try:
        # go through all rows of users
        for row in cursor.execute(
            f"SELECT Name, App FROM team WHERE Name = ('{interaction.user.display_name}') "
        ):
            if row != None:
                app = True
                if "TRUE" in str(row):  # if already clocked in
                    await interaction.response.send_message(
                        f"You already clocked in {interaction.user.display_name}"
                    )
                else:
                    cursor.execute(
                        f"UPDATE team SET App = 'TRUE', ClockIN = {int(time.time())} WHERE Name = ('{interaction.user.display_name}')"
                    )
                    database.commit()

                    await interaction.response.send_message(
                        f"Clocked in {interaction.user.display_name}"
                    )
    except Exception as e:
        print(f"Error syncing commands: {e}")

    # if user not clocked in
    if app == False:
        query = "INSERT INTO team VALUES(?, ?, ?, ?, ?, ?, 'FALSE')"

        if (
            discord.utils.get(interaction.guild.roles, name="software")
            in interaction.user.roles
        ):
            cursor.execute(
                query,
                (interaction.user.display_name, 0, int(time.time()), "TRUE", 0, "SOFTWARE"),
            )

        elif (
            discord.utils.get(interaction.guild.roles, name="business & outreach")
            in interaction.user.roles
        ):
            cursor.execute(
                query, (interaction.user.display_name, 0, int(time.time()), "TRUE", 0, "B&O")
            )

        elif (
            discord.utils.get(interaction.guild.roles, name="mechanical")
            in interaction.user.roles
        ):
            cursor.execute(
                query,
                (interaction.user.display_name, 0, int(time.time()), "TRUE", 0, "MECHANICAL"),
            )

        else:
            cursor.execute(
                query, (interaction.user.display_name, 0, int(time.time()), "TRUE", 0, "IDK")
            )

        database.commit()

        await interaction.response.send_message(f"Clocked in {interaction.user.display_name}")


@client.tree.command(
    name="clockout", description="Clock out (stop your timer)", guild=GUILD_ID
)  # Create a slash command
async def clockOut(interaction: discord.Interaction):
    # function to clockout users

    # check if user is clocked in
    if not checkClockedIn(interaction.user.display_name):
        await interaction.response.send_message(
            f"You are not clocked in {interaction.user.display_name}"
        )
        return

    # access the leads only channel where clock out request will be sent
    Channel = client.get_channel(CHAN)
    print(int(time.time()))

    # get user's clock in time from database
    cursor.execute(f"SELECT ClockIn FROM team WHERE Name = ('{interaction.user.display_name}')")
    clockInTime = cursor.fetchone()

    # error catching for no clockin time (most likely not needed)
    if clockInTime is None:
        await interaction.response.send_message(
            f"Error: Clock-in time not found for {interaction.user.display_name}."
        )
        return

    clockInTime = clockInTime[0]  # get clockin time stamp

    timeWorked = int(time.time()) - clockInTime
    formattedTimeWorked = convert(timeWorked)  # convert function to readable time

    # set clockout request time, make checking if clocked in (APP) false
    cursor.execute(
        f"UPDATE team SET Request = {int(time.time())}, App = FALSE WHERE Name = ('{interaction.user.display_name}')"
    )
    # send the request in the admin channel and wait
    view = MyView()
    await interaction.response.send_message(
        f"Your request for clocking out has been sent."
    )
    await Channel.send(
        f"**{interaction.user.display_name}** has sent in a request to clock out. "
        f"They have worked for {formattedTimeWorked} so far in this session. "
        f"Do you want to approve or deny time?",
        view=view,
    )
    await view.wait()

    # if no decision -> do nothing
    if view.value is None:
        return
    # if permitted -> update the time based on the clock in and clockout times
    elif view.value == True:
        cursor.execute(
            f"Select Total, ClockIn, Request FROM team WHERE Name = ('{interaction.user.display_name}')"
        )

        for row in cursor.fetchall():
            oldTime = row[0]
            clockInTime = row[1]
            request = row[2]

        newTime = request - clockInTime + oldTime

        cursor.execute(
            f"UPDATE team SET App = 'FALSE', Total = {newTime} WHERE Name = ('{interaction.user.display_name}')"
        )
        database.commit()

        timeInHours = convertToHours(newTime)

        #add to spreadsheet as well
        createNewCalendar(interaction.user.display_name, timeInHours)

        await interaction.channel.send(
            f"Thank you {interaction.user.display_name}, you worked for {convert(int(request - clockInTime))}"
        )
    # if denied
    else:
        # only update clocked in status, send message of no approval
        cursor.execute(
            f"UPDATE team SET App = 'FALSE' WHERE Name = ('{interaction.user.display_name}')"
        )
        database.commit()
        await interaction.channel.send(
            f"{interaction.user.display_name} your request was not approved"
        )


@client.tree.command(
    name="leave", description="Used To Leave If Clocked In By Accident", guild=GUILD_ID
)
async def leave(interaction: discord.Interaction):
    # function to leave without needing permission
    cursor.execute(
        f"UPDATE team SET App = 'FALSE' WHERE Name = ('{interaction.user.display_name}')"
    )  # makes 1 person's App column false
    database.commit()
    await interaction.response.send_message(f"Great you left {interaction.user.display_name}")


# same as clockout except goes through column of all people with App = True
@client.tree.command(
    name="forceclockout",
    description="Used to force everyone to request clock-out with their times",
    guild=GUILD_ID,
)
async def forceClockout(interaction: discord.Interaction):
    # need management role
    if discord.utils.get(interaction.user.roles, name="management") is None:
        await interaction.response.send_message("You do not have permission to use this command.")
        return

    # fetch all users who are currently clocked in
    cursor.execute(f"SELECT Name FROM team WHERE App = 'TRUE'")
    users_to_clockout = cursor.fetchall()

    if not users_to_clockout:
        await interaction.response.send_message("No users are currently clocked in.")
        return

    await interaction.response.send_message(f"Starting to process clock-out requests for {len(users_to_clockout)} users.")

    for user_row in users_to_clockout:
        user_name = user_row[0]

        cursor.execute(f"SELECT ClockIn FROM team WHERE Name = ('{user_name}')")
        clock_in_data = cursor.fetchone()
        if clock_in_data is None:
            continue

        clock_in_time = clock_in_data[0]
        time_worked = int(time.time()) - clock_in_time
        formatted_time_worked = convert(time_worked)

        cursor.execute(
            f"UPDATE team SET Request = {int(time.time())} WHERE Name = ('{user_name}')"
        )
        database.commit()

        Channel = client.get_channel(CHAN)
        view = MyView()

        await Channel.send(
            f"**{user_name}** has been forcefully requested to clock out. "
            f"They have worked for {formatted_time_worked} so far in this session. "
            f"Do you want to approve or deny time?",
            view=view,
        )
        await view.wait()

        if view.value is None:
            continue  
        elif view.value:  
            cursor.execute(
                f"SELECT Total, ClockIn, Request FROM team WHERE Name = ('{user_name}')"
            )
            for row in cursor.fetchall():
                old_time = row[0]
                clock_in_time = row[1]
                request_time = row[2]

            new_time = request_time - clock_in_time + old_time
            cursor.execute(
                f"UPDATE team SET App = 'FALSE', Total = {new_time} WHERE Name = ('{user_name}')"
            )
            database.commit()

            time_in_hours = convertToHours(new_time)
            createNewCalendar(user_name, time_in_hours)

            await Channel.send(
                f"Approved: {user_name} worked for {convert(request_time - clock_in_time)}."
            )
        else: 
            cursor.execute(
                f"UPDATE team SET App = 'FALSE' WHERE Name = ('{user_name}')"
            )
            database.commit()
            await Channel.send(f"Denied: {user_name}'s request was not approved.")

    await interaction.channel.send("All clock-out requests have been processed.")


# runs the bot
client.run(TOKEN)
