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
    print(f"Selected Title: {title}, URL: {url}")
    st.write(f"Selected Title: {title}")
    st.write(f"YouTube URL: {url}")

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
        st.session_state.df=get_df_from_messages(messages)

    if 'df' in st.session_state:
        event=st.dataframe(
            st.session_state.df,
            on_select='rerun',
            hide_index=True,
            selection_mode='multi-row'
        )

        print(f"Event: {event}")
        if len(event.selection['rows'])>0:
            print(f"Selected Rows: {event.selection['rows']}")
            row_index=event.selection['rows'][0]
            title=st.session_state.df.iloc[row_index]['Title']
            url=st.session_state.df.iloc[row_index]['YouTube URL']
            handle_selection(title, url)

if __name__ == '__main__':
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        main_page()
    else:
        authenticate()     