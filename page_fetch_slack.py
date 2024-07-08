import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import pandas as pd
import json
from google.oauth2 import service_account
import hashlib

from google_firestore import check_and_add_zoom_session, fetch_document_id, update_session_field_by_id
from generate_transcript import transcribe_session


# Initialize Slack client with your bot token
slack_token = st.secrets['SLACK_BOT_TOKEN']
client = WebClient(token=slack_token)

def fetch_channels():
    try:
        response = client.conversations_list()
        channels = response['channels']
        #st.write(f"Channels: {channels}")
        #print(f"Channels: {channels}")
        return channels
    except SlackApiError as e:
        st.error(f"Error fetching channels: {e.response['error']}")
        return []

def fetch_messages(channel_id, start_time, end_time):
    st.write(f"FETCH MESSAGES: {channel_id}, {start_time.timestamp()}, {end_time.timestamp()}")
    print(f"FETCH MESSAGES: {channel_id}, {start_time.timestamp()}, {end_time.timestamp()}")
    try:
        response = client.conversations_history(
            channel=channel_id,
            oldest=start_time.timestamp(),
            latest=end_time.timestamp(),
            inclusive=True
        )
        messages = response['messages']
        return messages
    except SlackApiError as e:
        st.error(f"Error fetching messages: {e.response['error']}")
        return []
    
def get_df_from_messages(messages):
    # Extract relevant data
    data = []
    for message in messages:
        if message.get("subtype") == "bot_message":
            title = message["text"].replace("bot:", "")
            timestamp = datetime.fromtimestamp(float(message["ts"]))
            youtube_url = message["attachments"][0]["actions"][0]["url"]
            data.append({
                "Title": title,
                "Datetime": timestamp,
                "YouTube URL": youtube_url
            })
    return pd.DataFrame(data)

def make_clickable(title, url):
    #return f'<a href="{url}" target="_blank">{title}</a>'
    return f"[{title}] {url} "

def create_markdown_link(row):
    title=row['Title']
    link=row['YouTube URL']
    #return f"[{row['Title']}]({row['YouTube URL']})"
    return f'<a target="_blank" href="{link}">{title}</a>'

def handle_selection(title, url):
    #print(f"Selected Title: {title}, URL: {url}")
    st.write(f"Selected Title: {title}")
    st.write(f"YouTube URL: {url}")
    json_obj=fetch_document_id(st.session_state.credentials, url)
    #transcript=f"Document: {json_obj}"
    #st.write(f"Document: {json_obj}")
    doc_id=json_obj[0]['id']
    transcript=transcribe_session(url,st.secrets['ASSEMBLYAI_API_KEY'])
    #update_field_by_id(st.session_state.credentials, doc_id, 'transcript', transcript)
    update_session_field_by_id(st.session_state.credentials, doc_id, 'transcript', transcript, 'transcripted')
    st.write(transcript)

def get_google_cloud_credentials():
    # Get Google Cloud credentials from JSON file
    js1 = st.secrets["GOOGLE_KEY"]
    #print(" A-plus Google credentials JS: ", js1)
    credentials_dict=json.loads(js1)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)   
    return credentials

def process_slack_messages(credentials,messages):
    print(f"Start processing messages: {len(messages)}")
    #print(messages[0])
    for m in messages:
        if m['subtype'] != 'bot_message':
            continue
        #print(f"Message is: {m}")
        #print(f"Attachments is: {m['attachments']}")
        #print(f"Attachment 0 is: {m['attachments'][0]}")
        #print(f"Action is: {m['attachments'][0]['actions']}")
        title = m["text"].replace("bot:", "")
        timestamp = datetime.fromtimestamp(float(m["ts"]))
        youtube_url = m["attachments"][0]["actions"][0]["url"]
        hash_hex = hashlib.md5(f"{title}-{timestamp}-{youtube_url}".encode()).hexdigest()
        #print(f"Hash: {hash_hex} Title: {title} Timestamp: {timestamp} URL: {youtube_url} ")
        check_and_add_zoom_session(credentials,hash_hex, title, timestamp, youtube_url)


def authenticate():
    st.title("Authentication Required")
    password = st.text_input("Enter the access key:", type="password")
    if password == st.secrets["ACCESS_KEY"]:
        st.session_state["authenticated"] = True
        st.experimental_rerun()
    elif password:
        st.error("Invalid secret key")

def main_page():
    # Streamlit app layout
    st.sidebar.title('Slack Message Fetcher')
    credentials = get_google_cloud_credentials()

    # Fetch and display available channels
    if 'channels' not in st.session_state:
        st.session_state.channels = fetch_channels()
    channels = st.session_state.channels
    channel_options = {channel['name']: channel['id'] for channel in channels}
    channel_name = 'session-notifications'
    channel_id = channel_options[channel_name]


    start_date = st.sidebar.date_input('Start date', datetime.now())
    start_time = st.sidebar.time_input('Start time', datetime.now().time())
    end_date = st.sidebar.date_input('End date', datetime.now())
    end_time = st.sidebar.time_input('End time', datetime.now().time())

    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    if st.sidebar.button('<Fetch Messages>'):
        channel_id = channel_options[channel_name]
        messages = fetch_messages(channel_id, start_datetime, end_datetime)
        process_slack_messages(credentials, messages)
        st.session_state.df=get_df_from_messages(messages)

    if 'df' in st.session_state:
        df=st.session_state.df.copy()
        #df['Title'] = df.apply(lambda row: make_clickable(row['Title'], row['YouTube URL']), axis=1)
        #df_display = df[['Title', 'Datetime']]

        
        event=st.dataframe(
            df,
            on_select='rerun',
            hide_index=True,
            selection_mode='single-row'
        )

        print(f"Event: {event}")
        if len(event.selection['rows'])>0:
            print(f"Selected Rows: {event.selection['rows']}")
            row_index=event.selection['rows'][0]
            title=st.session_state.df.iloc[row_index]['Title']
            url=st.session_state.df.iloc[row_index]['YouTube URL']
            handle_selection(title, url)

#
# Main method for page
#
main_page()
