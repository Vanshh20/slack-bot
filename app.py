from flask import Flask, request, Response
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
DATABASE_URL = os.getenv('DATABASE_URL')

# Initialize Slack client and signature verifier
slack_client = WebClient(token=SLACK_BOT_TOKEN)
verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

# Initialize database
engine = create_engine(DATABASE_URL, connect_args={'sslmode': 'require'})
Session = sessionmaker(bind=engine)

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.start()

def verify_request():
    # Bypassing Slack authentication verification for now
    return True

def get_user_metrics(session, team_id, limit=5, timeframe='1 day'):
    query = text("""
        SELECT 
            user_id,
            SUM(message_count) as message_count,
            SUM(reaction_count) as reaction_count,
            AVG(response_time) as avg_response_time
        FROM metrics
        WHERE team_id = :team_id
        AND user_id != :bot_user_id
        AND recorded_at >= NOW() - INTERVAL :timeframe
        GROUP BY user_id
        ORDER BY message_count DESC, reaction_count DESC
        LIMIT :limit
    """)
    
    result = session.execute(query, {'team_id': team_id, 'timeframe': timeframe, 'limit': limit, 'bot_user_id': 'U097KCQHADC'}).fetchall()
    
    if not result:
        return []
        
    metrics = []
    for row in result:
        user_id, msg_count, react_count, avg_response = row
        avg_response_str = f"{avg_response:.2f}s" if avg_response else "N/A"
        metrics.append({
            'user_id': user_id,
            'message_count': int(msg_count),
            'reaction_count': int(react_count),
            'avg_response_time': avg_response_str
        })
    
    return metrics

def format_slack_message(metrics, header="Top Active Users", show_bottom=False, limit=None):
    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header}},
        {"type": "divider"}
    ]
    
    text_lines = []
    if metrics:
        for metric in metrics:
            line = f"*User <@{metric['user_id']}>:* 👁️ {metric['message_count']} messages, 👍 {metric['reaction_count']} reactions, ⏱️ {metric['avg_response_time']} avg response"
            text_lines.append(line)
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(text_lines)}})
    else:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "No user activity found."}})
    
    if show_bottom and limit:
        blocks.extend([
            {"type": "header", "text": {"type": "plain_text", "text": f"Bottom {limit} Active Users"}},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(reversed(text_lines[-limit:])) if text_lines else "No user activity found."}}
        ])
    
    text = "\n".join(text_lines) if text_lines else "No user activity found."
    return blocks, text

def send_weekly_report():
    from sqlalchemy import text  # Explicit import to avoid UnboundLocalError
    logger.info("Running scheduled weekly report")
    session = Session()
    try:
        teams = session.execute(text("SELECT DISTINCT team_id FROM metrics")).fetchall()
        for team in teams:
            team_id = team[0]
            report_channel = session.execute(
                text("SELECT channel_id FROM report_channels WHERE team_id = :team_id"),
                {'team_id': team_id}
            ).fetchone()
            channel_id = report_channel[0] if report_channel else "#general"

            # Fetch all users (no limit)
            metrics = get_user_metrics(session, team_id, limit=999999, timeframe='7 days')
            blocks, text = format_slack_message(
                metrics,
                header="Weekly Metrics Report"
            )

            try:
                slack_client.chat_postMessage(channel=channel_id, blocks=blocks, text=text)
                logger.info(f"Posted scheduled weekly report to team {team_id}, channel {channel_id}")
            except Exception as e:
                logger.error(f"Error sending weekly report for {team_id}: {e}")
    finally:
        session.close()

def send_monthly_report():
    from sqlalchemy import text  # Explicit import to avoid UnboundLocalError
    logger.info("Running scheduled monthly report")
    session = Session()
    try:
        teams = session.execute(text("SELECT DISTINCT team_id FROM metrics")).fetchall()
        for team in teams:
            team_id = team[0]
            report_channel = session.execute(
                text("SELECT channel_id FROM report_channels WHERE team_id = :team_id"),
                {'team_id': team_id}
            ).fetchone()
            channel_id = report_channel[0] if report_channel else "#general"

            # Fetch all users (no limit)
            metrics = get_user_metrics(session, team_id, limit=999999, timeframe='30 days')
            blocks, text = format_slack_message(
                metrics,
                header="Monthly Metrics Report"
            )

            try:
                slack_client.chat_postMessage(channel=channel_id, blocks=blocks, text=text)
                logger.info(f"Posted scheduled monthly report to team {team_id}, channel {channel_id}")
            except Exception as e:
                logger.error(f"Error sending monthly report for {team_id}: {e}")
    finally:
        session.close()

def send_yearly_report():
    from sqlalchemy import text  # Explicit import to avoid UnboundLocalError
    logger.info("Running scheduled yearly report")
    session = Session()
    try:
        teams = session.execute(text("SELECT DISTINCT team_id FROM metrics")).fetchall()
        for team in teams:
            team_id = team[0]
            report_channel = session.execute(
                text("SELECT channel_id FROM report_channels WHERE team_id = :team_id"),
                {'team_id': team_id}
            ).fetchone()
            channel_id = report_channel[0] if report_channel else "#general"

            # Fetch all users (no limit)
            metrics = get_user_metrics(session, team_id, limit=999999, timeframe='365 days')
            blocks, text = format_slack_message(
                metrics,
                header="Yearly Metrics Report"
            )

            try:
                slack_client.chat_postMessage(channel=channel_id, blocks=blocks, text=text)
                logger.info(f"Posted scheduled yearly report to team {team_id}, channel {channel_id}")
            except Exception as e:
                logger.error(f"Error sending yearly report for {team_id}: {e}")
    finally:
        session.close()

@app.route('/test-weekly-report', methods=['GET'])
def test_weekly_report():
    send_weekly_report()
    return "Weekly report triggered"

@app.route('/test-monthly-report', methods=['GET'])
def test_monthly_report():
    send_monthly_report()
    return "Monthly report triggered"

@app.route('/test-yearly-report', methods=['GET'])
def test_yearly_report():
    send_yearly_report()
    return "Yearly report triggered"

@app.route('/slack/install', methods=['GET'])
def install():
    client_id = os.getenv('SLACK_CLIENT_ID')
    install_url = f"https://slack.com/oauth/v2/authorize?client_id={client_id}&scope=channels:history,channels:read,chat:write,commands,reactions:read,users:read&user_scope="
    return f'<a href="{install_url}">Install to Slack</a>'

@app.route('/slack/oauth_redirect', methods=['GET'])
def oauth_redirect():
    code = request.args.get('code')
    client_id = os.getenv('SLACK_CLIENT_ID')
    client_secret = os.getenv('SLACK_CLIENT_SECRET')
    
    try:
        response = slack_client.oauth_v2_access(
            client_id=client_id,
            client_secret=client_secret,
            code=code
        )
        if response['ok']:
            team_id = response['team']['id']
            bot_token = response['access_token']
            
            with Session() as session:
                session.execute(
                    text("DELETE FROM slack_bots WHERE team_id = :team_id"),
                    {'team_id': team_id}
                )
                session.execute(
                    text("INSERT INTO slack_bots (team_id, bot_token, created_at) VALUES (:team_id, :bot_token, NOW())"),
                    {'team_id': team_id, 'bot_token': bot_token}
                )
                session.commit()
            
            return "App installed successfully!"
        else:
            return f"Error installing app: {response['error']}"
    except Exception as e:
        logger.error(f"Error during OAuth: {str(e)}")
        return f"Error during OAuth: {str(e)}"

@app.route('/slack/events', methods=['POST'])
def slack_events():
    if request.json.get('type') == 'url_verification':
        return request.json['challenge']
    
    if not verify_request():
        return Response("Invalid request signature", status=401)
    
    event = request.json.get('event', {})
    team_id = request.json.get('team_id')
    
    if event.get('type') == 'message' and 'subtype' not in event and 'bot_id' not in event:
        with Session() as session:
            user_id = event['user']
            channel_id = event['channel']
            message_ts = float(event['ts'])
            
            metric = session.execute(
                text("SELECT id FROM metrics WHERE team_id = :team_id AND user_id = :user_id AND channel_id = :channel_id"),
                {'team_id': team_id, 'user_id': user_id, 'channel_id': channel_id}
            ).fetchone()
            
            if metric:
                session.execute(
                    text("UPDATE metrics SET message_count = message_count + 1, recorded_at = NOW() WHERE id = :id"),
                    {'id': metric[0]}
                )
            else:
                session.execute(
                    text("INSERT INTO metrics (team_id, user_id, channel_id, message_count, reaction_count, recorded_at) VALUES (:team_id, :user_id, :channel_id, 1, 0, NOW())"),
                    {'team_id': team_id, 'user_id': user_id, 'channel_id': channel_id}
                )
            
            if event.get('thread_ts'):
                parent_ts = float(event['thread_ts'])
                response_time = message_ts - parent_ts
                session.execute(
                    text("UPDATE metrics SET response_time = :response_time WHERE team_id = :team_id AND user_id = :user_id AND channel_id = :channel_id"),
                    {'team_id': team_id, 'user_id': user_id, 'channel_id': channel_id, 'response_time': response_time}
                )
            
            session.commit()
            logger.info(f"Recorded message for user {user_id} in channel {channel_id}")
    
    elif event.get('type') == 'reaction_added':
        with Session() as session:
            user_id = event['user']
            channel_id = event['item']['channel']
            
            metric = session.execute(
                text("SELECT id FROM metrics WHERE team_id = :team_id AND user_id = :user_id AND channel_id = :channel_id"),
                {'team_id': team_id, 'user_id': user_id, 'channel_id': channel_id}
            ).fetchone()
            
            if metric:
                session.execute(
                    text("UPDATE metrics SET reaction_count = reaction_count + 1, recorded_at = NOW() WHERE id = :id"),
                    {'id': metric[0]}
                )
            else:
                session.execute(
                    text("INSERT INTO metrics (team_id, user_id, channel_id, message_count, reaction_count, recorded_at) VALUES (:team_id, :user_id, :channel_id, 0, 1, NOW())"),
                    {'team_id': team_id, 'user_id': user_id, 'channel_id': channel_id}
                )
            
            session.commit()
            logger.info(f"Recorded reaction for user {user_id} in channel {channel_id}")
    
    return Response(status=200)

@app.route('/slack/metrics', methods=['POST'])
def metrics():
    logger.debug(f"Metrics command request received: {request.form}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    if not verify_request():
        return Response("Invalid request signature", status=401)
    
    team_id = request.form.get('team_id')
    channel_id = request.form.get('channel_id')
    command_text = request.form.get('text', '').strip().split()
    
    with Session() as session:
        if not command_text:
            metrics = get_user_metrics(session, team_id, limit=5)
            blocks, text = format_slack_message(metrics, show_bottom=True, limit=5)
        elif command_text[0] == 'weekly':
            try:
                limit = int(command_text[1]) if len(command_text) > 1 else 5
                metrics = get_user_metrics(session, team_id, limit=limit, timeframe='7 days')
                blocks, text = format_slack_message(metrics, header=f"Weekly Metrics Report (Top {limit} Active Users)", show_bottom=True, limit=limit)
            except ValueError:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="Invalid number. Usage: `/metrics weekly [number]` (e.g., `/metrics weekly 5`)",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Invalid number. Usage: `/metrics weekly [number]` (e.g., `/metrics weekly 5`)"}}]
                )
                logger.warning(f"Invalid weekly command received: {command_text}")
                return Response(status=200)
        elif command_text[0] == 'monthly':
            try:
                limit = int(command_text[1]) if len(command_text) > 1 else 5
                metrics = get_user_metrics(session, team_id, limit=limit, timeframe='30 days')
                blocks, text = format_slack_message(metrics, header=f"Monthly Metrics Report (Top {limit} Active Users)", show_bottom=True, limit=limit)
            except ValueError:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="Invalid number. Usage: `/metrics monthly [number]` (e.g., `/metrics monthly 5`)",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Invalid number. Usage: `/metrics monthly [number]` (e.g., `/metrics monthly 5`)"}}]
                )
                logger.warning(f"Invalid monthly command received: {command_text}")
                return Response(status=200)
        elif command_text[0] == 'yearly':
            try:
                limit = int(command_text[1]) if len(command_text) > 1 else 5
                metrics = get_user_metrics(session, team_id, limit=limit, timeframe='365 days')
                blocks, text = format_slack_message(metrics, header=f"Yearly Metrics Report (Top {limit} Active Users)", show_bottom=True, limit=limit)
            except ValueError:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="Invalid number. Usage: `/metrics yearly [number]` (e.g., `/metrics yearly 5`)",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Invalid number. Usage: `/metrics yearly [number]` (e.g., `/metrics yearly 5`)"}}]
                )
                logger.warning(f"Invalid yearly command received: {command_text}")
                return Response(status=200)
        elif command_text[0] == 'top_users':
            try:
                limit = int(command_text[1]) if len(command_text) > 1 else 5
                metrics = get_user_metrics(session, team_id, limit=limit)
                blocks, text = format_slack_message(metrics, header=f"Top {limit} Active Users")
            except ValueError:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="Invalid number. Usage: `/metrics top_users [number]` (e.g., `/metrics top_users 5`)",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Invalid number. Usage: `/metrics top_users [number]` (e.g., `/metrics top_users 5`)"}}]
                )
                logger.warning(f"Invalid top_users command received: {command_text}")
                return Response(status=200)
        else:
            try:
                limit = int(command_text[0])
                metrics = get_user_metrics(session, team_id, limit=limit)
                blocks, text = format_slack_message(metrics, show_bottom=True, limit=limit)
            except ValueError:
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text="Invalid command. Usage: `/metrics [number]`, `/metrics weekly [number]`, `/metrics monthly [number]`, `/metrics yearly [number]`, or `/metrics top_users [number]` (e.g., `/metrics 5`)",
                    blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": "Invalid command. Usage: `/metrics [number]`, `/metrics weekly [number]`, `/metrics monthly [number]`, `/metrics yearly [number]`, or `/metrics top_users [number]` (e.g., `/metrics 5`)"}}]
                )
                logger.warning(f"Invalid command received: {command_text}")
                return Response(status=200)
        
        try:
            slack_client.chat_postMessage(channel=channel_id, blocks=blocks, text=text)
            logger.info(f"Posted metrics report to team {team_id}, channel {channel_id}")
        except Exception as e:
            logger.error(f"Failed to post metrics report: {str(e)}")
            return Response(f"Error posting metrics: {str(e)}", status=500)
        
        return Response(status=200)

@app.route('/slack/set-report-channel', methods=['POST'])
def set_report_channel():
    logger.debug(f"Set-report-channel request received: {request.form}")
    logger.debug(f"Headers: {dict(request.headers)}")
    
    if not verify_request():
        return Response("Invalid request signature", status=401)
    
    team_id = request.form.get('team_id')
    channel_id = request.form.get('channel_id')
    channel_name = request.form.get('channel_name')
    
    with Session() as session:
        session.execute(
            text("INSERT INTO report_channels (team_id, channel_id, created_at) VALUES (:team_id, :channel_id, NOW()) ON CONFLICT (team_id) DO UPDATE SET channel_id = :channel_id, created_at = NOW()"),
            {'team_id': team_id, 'channel_id': channel_id}
        )
        session.commit()
    
    try:
        slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Weekly reports will now be posted to #{channel_name}.",
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": f"Weekly reports will now be posted to #{channel_name}."}}]
        )
        logger.info(f"Set report channel for team {team_id} to {channel_id} (#{channel_name})")
    except Exception as e:
        logger.error(f"Failed to post channel confirmation: {str(e)}")
        return Response(f"Error setting report channel: {str(e)}", status=500)
    
    return Response(status=200)

# Schedule reports
scheduler.add_job(
    send_weekly_report,
    trigger=CronTrigger(day_of_week='mon', hour=9, minute=0, timezone='Asia/Kolkata'),
    id='weekly_report'
)
scheduler.add_job(
    send_monthly_report,
    trigger=CronTrigger(day='1', hour=9, minute=0, timezone='Asia/Kolkata'),
    id='monthly_report'
)
scheduler.add_job(
    send_yearly_report,
    trigger=CronTrigger(day='1', month='1', hour=9, minute=0, timezone='Asia/Kolkata'),
    id='yearly_report'
)

if __name__ == '__main__':
    app.run(debug=True)