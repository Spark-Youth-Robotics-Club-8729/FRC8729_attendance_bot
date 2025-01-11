# Discord Attendance Bot

![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)

This is a discord bot, built by [Lucas J.](https://github.com/LucasHJin) and [Dylan C.](https://github.com/RaiiClouds), for **FRC Team 8729 Sparkling H2O**. It tracks the attendance for every member in the discord server and writes all this data to both a local database and a google spreadsheet. It is written to be able to be forked and used by other teams with a few simple steps.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [License](#license)

## Installation
1. Clone the repo: 
`git clone https://github.com/LucasHJin/FRC8729_attendance_bot.git`
2. Navigate to the project folder: 
`cd FRC8729_attendance_bot`
3. Install dependencies: 
`pip install -r requirements.txt`
4. Delete the information in the local database to start fresh
5. Create a discord bot ([visit this link for more information](https://discord.com/developers/applications))
   - Create a `.env` file in the directory of the cloned repo and enter the values for `TOKEN`, `ID`, and `CHAN`
     - `TOKEN`: The bot's authentication token
     - `ID`: The discord server ID where you want to use the bot
     - `CHAN`: The channel where the bot's messages will be sent (an admin/lead only channel)
6. Create a spreadsheet where the attendance data will be written to
   - Visit [Google Cloud Console](https://console.cloud.google.com/apis/library/sheets.googleapis.com) to enable the spreadsheet API and create a project
   - Within that project, create a Service Account credential and download the JSON authentication key
     - Move that JSON file into your directory and update the following code with your JSON's file name
```python
creds = Credentials.from_service_account_file(
    "CHANGE THIS VALUE",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
```
7. (Optional) Consider hosting your discord bot on a hosting service like [bot-hosting](https://bot-hosting.net/)

## Usage 
### Functions
![Robot Functions](assets/Robot%20Functions.png)

**Clockin**: Clocks the member in and starts tracking their time.

**Clockout**: Creates a request from the member to clockout and pauses their time. The request is sent in the specified (admin only) channel where it can either be denied or accepted.

**List**: Lists all the members from a specific subteam and how many hours each of them have tracked down so far.

**Leave**: Allows a member to leave without needing to prompt the leads to clockout if they accidentally clocked in.

**ForceClockout**: Forces everybody who is currently clocked in to clock out. Everyone will have a request sent for their time to be clocked out. This can only be used by someone with the role *management*. It is useful as a final backup to clockout anybody that may have forgotten.
 
### Written Data
**Main Page**: This is the page where every single member's hours are tracked.
![Main Page](assets/Main%20Page.png)

**Specific Member's Page**: This is a specific page (new sheet) tracking how many hours a member worked during any one time.
![Calendar Page](assets/Calendar%20Page.png)

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.