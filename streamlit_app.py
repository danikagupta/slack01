import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import pandas as pd
import json


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

def handle_selection(title, url):
    st.write(f"Selected Title: {title}")
    st.write(f"YouTube URL: {url}")

css = """
<style>
    .stColumn {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    .stButton button {
        width: 100%;
    }
</style>
"""

# Inject CSS with Markdown
st.markdown(css, unsafe_allow_html=True)

# Streamlit app layout
st.sidebar.title('Slack Message Fetcher')

# Fetch and display available channels
channels = fetch_channels()
channel_options = {channel['name']: channel['id'] for channel in channels}

if channel_options:
    #channel_name = st.selectbox('Select a Slack channel:', list(channel_options.keys()))
    channel_name = 'session-notifications'
    start_date = st.sidebar.date_input('Start date', datetime.now())
    start_time = st.sidebar.time_input('Start time', datetime.now().time())
    end_date = st.sidebar.date_input('End date', datetime.now())
    end_time = st.sidebar.time_input('End time', datetime.now().time())

    start_datetime = datetime.combine(start_date, start_time)
    end_datetime = datetime.combine(end_date, end_time)

    if st.sidebar.button('<Fetch Messages>'):
        channel_id = channel_options[channel_name]
        messages = fetch_messages(channel_id, start_datetime, end_datetime)
        #pm = json.dumps(messages[:5],indent=2)
        #print(f"*****\n******\n*****\nMessages: {pm}")
        df=get_df_from_messages(messages)

        col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
        col1.markdown('<p class="stColumn"><strong>Meeting</strong></p>', unsafe_allow_html=True)
        col2.markdown('<p class="stColumn"><strong>Date Time </strong></p>', unsafe_allow_html=True)
        col3.markdown('<p class="stColumn"><strong>Action</strong></p>', unsafe_allow_html=True)
        col4.markdown('<p class="stColumn"><strong>Action</strong></p>', unsafe_allow_html=True)

        
        for index,row in df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
            with col1:
                st.markdown(f'<p class="stColumn">{row["Title"]}</p>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<p class="stColumn">{row["Datetime"]}</p>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<p class="stColumn">{row["YouTube URL"]}</p>', unsafe_allow_html=True)
            with col4:
                st.markdown('<div class="stColumn">', unsafe_allow_html=True)
                st.button(row['Title'], key=f"direct_button_{index}",on_click=handle_selection, args=[row['Title'], row['YouTube URL']])
                st.markdown('</div>', unsafe_allow_html=True)
            #col1.write(row['Title'])
            #col2.write(row['Datetime'])
            #col3.write(row['YouTube URL'])
            #col4.button(row['Title'], key=f"direct_button_{index}",on_click=handle_selection, args=[row['Title'], row['YouTube URL']])

