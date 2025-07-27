Slack Engagement Bot
 A Slack bot to track workspace engagement and generate reports, hosted on Render.

 ## Setup
 1. Clone the repository: `git clone https://github.com/Vanshh20/slack-bot.git`
 2. Install dependencies: `pip install -r requirements.txt`
 3. Set up environment variables in `.env` with Slack and Supabase credentials.
 4. Configure a Slack App with OAuth, event subscriptions, and slash commands.
 5. Set up a PostgreSQL database via Supabase.
 6. Run locally for testing: `python app.py`
 7. Deploy to Render:
    - Create a Web Service, connect to `Vanshh20/slack-bot`.
    - Set environment variables in Render dashboard.
    - Use `pip install -r requirements.txt` as build command and `gunicorn app:app` as start command.

 ## Usage
 - Install the bot via `/slack/install`.
 - Use `/metrics weekly [number]` to get top/bottom user reports (e.g., `/metrics weekly 5`).
 - Weekly reports are scheduled every Monday at 9 AM.

 ## Extending
 - Add more slash commands in `app.py`.
 - Implement response time tracking for thread replies.
