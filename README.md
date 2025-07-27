# Slack Engagement Bot

A Slack bot for tracking workspace engagement and generating comprehensive reports on user activity. The bot monitors messages, reactions, and response times, and sends scheduled weekly, monthly, and yearly reports to designated Slack channels. It is designed to be hosted on Render and uses a PostgreSQL database (via Supabase) for storing metrics.

## Features

- Tracks user engagement metrics: message count, reaction count, and average response time for thread replies.
- Generates scheduled reports:
  - Weekly reports every Monday at 9:00 AM IST.
  - Monthly reports on the 1st of each month at 9:00 AM IST.
  - Yearly reports on January 1st at 9:00 AM IST.
- Reports include metrics for **all users** in the specified timeframe.
- Supports slash commands for on-demand metrics reports.
- Stores data in a PostgreSQL database via Supabase.
- Deployable on Render with easy setup.

## Setup

### Prerequisites

- Python 3.11 or higher
- A Slack workspace with admin access to create and install a Slack App
- A Supabase account for PostgreSQL database hosting
- A Render account for deployment
- Git installed for cloning the repository
- A GitHub account with the repository pushed (already done at `https://github.com/Vanshh20/slack-bot`)

### Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Vanshh20/slack-bot.git
   cd slack-bot
   ```

2. **Install Dependencies**:
   Install the required Python packages using the provided `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the project root and add the following variables:
   ```bash
   SLACK_BOT_TOKEN=your-slack-bot-token
   SLACK_SIGNING_SECRET=your-slack-signing-secret
   SLACK_CLIENT_ID=your-slack-client-id
   SLACK_CLIENT_SECRET=your-slack-client-secret
   DATABASE_URL=your-supabase-postgresql-url
   ```
   - `SLACK_BOT_TOKEN`: Obtained from your Slack App’s “OAuth & Permissions” section (Bot User OAuth Token).
   - `SLACK_SIGNING_SECRET`: Found in your Slack App’s “Basic Information” section.
   - `SLACK_CLIENT_ID` and `SLACK_CLIENT_SECRET`: Also found in the “Basic Information” section of your Slack App.
   - `DATABASE_URL`: The PostgreSQL connection string from your Supabase project (e.g., `postgresql://user:password@host:port/dbname`).

4. **Configure the Slack App**:
   - Create a Slack App in your workspace via the [Slack API](https://api.slack.com/apps).
   - Add the following bot token scopes under “OAuth & Permissions”:
     - `channels:history`
     - `channels:read`
     - `chat:write`
     - `commands`
     - `reactions:read`
     - `users:read`
   - Enable Event Subscriptions and subscribe to the following bot events:
     - `message.channels`
     - `reaction_added`
   - Add a slash command (e.g., `/metrics`) with the request URL set to `https://your-render-url/slack/metrics`.
   - Add another slash command (e.g., `/set-report-channel`) with the request URL set to `https://your-render-url/slack/set-report-channel`.
   - Set the “Install App” URL to `https://your-render-url/slack/install` for OAuth installation.

5. **Set Up the PostgreSQL Database**:
   - Create a Supabase project and obtain the PostgreSQL connection string.
   - Create the following tables in your Supabase database:
     ```sql
     CREATE TABLE metrics (
         id SERIAL PRIMARY KEY,
         team_id TEXT NOT NULL,
         user_id TEXT NOT NULL,
         channel_id TEXT NOT NULL,
         message_count INTEGER DEFAULT 0,
         reaction_count INTEGER DEFAULT 0,
         response_time FLOAT,
         recorded_at TIMESTAMP NOT NULL
     );

     CREATE TABLE report_channels (
         team_id TEXT PRIMARY KEY,
         channel_id TEXT NOT NULL,
         created_at TIMESTAMP NOT NULL
     );

     CREATE TABLE slack_bots (
         team_id TEXT PRIMARY KEY,
         bot_token TEXT NOT NULL,
         created_at TIMESTAMP NOT NULL
     );
     ```
   - Ensure the database is accessible using the `DATABASE_URL` from your `.env` file.

6. **Run Locally for Testing**:
   Start the Flask development server:
   ```bash
   python app.py
   ```
   Use a tool like `ngrok` to expose your local server for Slack event testing:
   ```bash
   ngrok http 5000
   ```
   Update your Slack App’s event subscription and slash command URLs to use the `ngrok` URL (e.g., `https://your-ngrok-url/slack/events`).

## Installation

1. **Install the Bot to Your Slack Workspace**:
   - Access the `/slack/install` endpoint (e.g., `http://localhost:5000/slack/install` locally or `https://your-render-url/slack/install` on Render).
   - Follow the OAuth flow to install the bot to your Slack workspace.
   - This will store the bot’s token in the `slack_bots` table for the team.

2. **Set the Report Channel**:
   - Use the `/set-report-channel` slash command in your desired Slack channel to designate it for scheduled reports:
     ```slack
     /set-report-channel
     ```
   - This updates the `report_channels` table to send weekly, monthly, and yearly reports to the specified channel. If not set, reports default to the `#general` channel.

## Deploying to Render

1. **Create a Web Service on Render**:
   - Log in to your Render account and create a new Web Service.
   - Connect to your GitHub repository: `https://github.com/Vanshh20/slack-bot`.
   - Select the branch containing your code (e.g., `main`).

2. **Configure Environment Variables**:
   - In the Render dashboard, add the following environment variables under the Web Service settings:
     ```
     SLACK_BOT_TOKEN=your-slack-bot-token
     SLACK_SIGNING_SECRET=your-slack-signing-secret
     SLACK_CLIENT_ID=your-slack-client-id
     SLACK_CLIENT_SECRET=your-slack-client-secret
     DATABASE_URL=your-supabase-postgresql-url
     ```
   - Ensure these match the values used in local testing.

3. **Set Build and Start Commands**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

4. **Deploy**:
   - Trigger a deployment in Render. Once deployed, note the Render URL (e.g., `https://your-app-name.onrender.com`).
   - Update your Slack App’s event subscription and slash command URLs to use the Render URL:
     - Event Subscription: `https://your-app-name.onrender.com/slack/events`
     - Slash Command (`/metrics`): `https://your-app-name.onrender.com/slack/metrics`
     - Slash Command (`/set-report-channel`): `https://your-app-name.onrender.com/slack/set-report-channel`
     - OAuth Install URL: `https://your-app-name.onrender.com/slack/install`

5. **Verify Deployment**:
   - Test the `/slack/install` endpoint to install the bot.
   - Use the `/metrics` command in Slack to verify functionality.
   - Check Render logs for any errors during startup or operation.

## Usage

### Slash Commands

- **View Metrics**:
  - `/metrics`: Displays the top 5 active users for the past 24 hours (default).
  - `/metrics [number]`: Shows the top and bottom `number` users for the past 24 hours (e.g., `/metrics 10`).
  - `/metrics weekly [number]`: Shows the top and bottom `number` users for the past 7 days (e.g., `/metrics weekly 5`).
  - `/metrics monthly [number]`: Shows the top and bottom `number` users for the past 30 days.
  - `/metrics yearly [number]`: Shows the top and bottom `number` users for the past 365 days.
  - `/metrics top_users [number]`: Shows the top `number` users for the past 24 hours.

- **Set Report Channel**:
  - `/set-report-channel`: Sets the current channel as the destination for scheduled reports.

### Scheduled Reports

- **Weekly Report**: Sent every Monday at 9:00 AM IST to the designated channel (or `#general` if not set). Includes metrics for **all users** active in the past 7 days.
- **Monthly Report**: Sent on the 1st of each month at 9:00 AM IST. Includes metrics for **all users** active in the past 30 days.
- **Yearly Report**: Sent on January 1st at 9:00 AM IST. Includes metrics for **all users** active in the past 365 days.

### Testing Reports Locally

- Use the following endpoints to trigger reports manually:
  - `GET /test-weekly-report`: Triggers a weekly report.
  - `GET /test-monthly-report`: Triggers a monthly report.
  - `GET /test-yearly-report`: Triggers a yearly report.
  - Example: `curl http://localhost:5000/test-weekly-report`

## Extending

To extend the bot’s functionality, modify the `app.py` file. Here are some suggestions:

1. **Add New Slash Commands**:
   - Add a new route in `app.py` under the `/slack/metrics` route’s structure.
   - Example: To add a `/stats` command for channel-specific metrics:
     ```python
     @app.route('/slack/stats', methods=['POST'])
     def stats():
         if not verify_request():
             return Response("Invalid request signature", status=401)
         team_id = request.form.get('team_id')
         channel_id = request.form.get('channel_id')
         # Add logic to fetch and format channel-specific metrics
         return Response(status=200)
     ```
   - Update your Slack App to include the new command with the request URL (e.g., `https://your-render-url/slack/stats`).

2. **Enhance Response Time Tracking**:
   - Improve the `slack_events` route to calculate more precise response times or track additional metrics (e.g., thread participation rates).
   - Example: Add a new column to the `metrics` table and update the `INSERT`/`UPDATE` queries in the `message` event handler.

3. **Custom Report Formats**:
   - Modify `format_slack_message` to include additional fields or change the report layout (e.g., add emojis, charts, or user names).
   - Ensure the function remains compatible with Slack’s block kit format.

4. **Additional Scheduled Reports**:
   - Add new scheduled jobs in the `scheduler.add_job` section of `app.py`.
   - Example: Add a daily report:
     ```python
     scheduler.add_job(
         send_daily_report,  # Define a new send_daily_report function
         trigger=CronTrigger(hour=9, minute=0, timezone='Asia/Kolkata'),
         id='daily_report'
     )
     ```

5. **Database Enhancements**:
   - Add new tables or columns to store additional metrics (e.g., message types, file uploads).
   - Update the `metrics` table schema and corresponding queries in `get_user_metrics`.

6. **Error Handling**:
   - Enhance logging in `app.py` to capture more detailed error information.
   - Add retry logic for Slack API calls using a library like `tenacity`.

## Troubleshooting

- **UnboundLocalError for `text`**:
  - Ensure the `sqlalchemy` package is installed (`pip show sqlalchemy`).
  - Verify no other scripts or imports are shadowing the `text` function from `sqlalchemy`.
- **Database Connection Issues**:
  - Check that `DATABASE_URL` is correct and the Supabase database is accessible.
  - Test the connection locally using a tool like `psql`.
- **Slack API Errors**:
  - Verify that all required scopes are added to the Slack App.
  - Check Render logs for Slack API response errors.
- **Reports Not Sending**:
  - Ensure the `metrics` and `report_channels` tables contain data.
  - Test manual report triggers (`/test-weekly-report`, etc.) to debug.
- **Scheduler Issues**:
  - Confirm the `apscheduler` package is installed.
  - Check Render logs to ensure the scheduler is running.

## Dependencies

The bot relies on the following Python packages (listed in `requirements.txt`):
- `flask`: Web framework for handling HTTP requests.
- `slack_sdk`: Slack API client for interacting with Slack.
- `sqlalchemy`: Database ORM for PostgreSQL interactions.
- `python-dotenv`: Loads environment variables from `.env`.
- `apscheduler`: Schedules recurring reports.
- `gunicorn`: WSGI server for Render deployment.

## About

This Slack Engagement Bot was developed to help workspace administrators track user activity and generate detailed engagement reports. It is deployed on Render and uses Supabase for data storage. For issues or contributions, please open a pull request or issue on the [GitHub repository](https://github.com/Vanshh20/slack-bot).