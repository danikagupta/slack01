import streamlit as st
import pandas as pd
from google.cloud import firestore

from google_firestore import fetch_sessions_with_transcripts

# Initialize Firestore client
db = firestore.Client(credentials=st.session_state.credentials)

# Function to fetch records from Firestore collection
def fetch_records(collection_name):
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()
    
    # Convert Firestore documents to a list of dictionaries
    #records = [doc.to_dict() for doc in docs]
    records = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return records

def handle_selection(title, url):
    #print(f"Selected Title: {title}, URL: {url}")
    st.write(f"Selected Title: {title}")
    st.write(f"YouTube URL: {url}")

# Main function to display records in Streamlit
def main():
    st.title("Session Viewer")
    
    # Fetch records from Firestore collection
    #collection_name = "sessions"
    #records = fetch_records(collection_name)
    
    # Convert records to DataFrame
    #df = pd.DataFrame(records)
    #df['Transcript available']=df['transcript'].notnull()

    records=fetch_sessions_with_transcripts(st.session_state.credentials)
    df=pd.DataFrame(records)
    
    # Display DataFrame in Streamlit
    event=st.dataframe(df,
                column_config={
                'id':None,
                'transcript':None,
                'status':None,
                },
                use_container_width=True,
                on_select='rerun',
                hide_index=True,
                selection_mode='single-row')
    print(f"Event: {event}")
    if len(event.selection['rows'])>0:
        print(f"Selected Rows: {event.selection['rows']}")
        row_index=event.selection['rows'][0]
        title=st.session_state.df.iloc[row_index]['Title']
        url=st.session_state.df.iloc[row_index]['YouTube URL']
        handle_selection(title, url)

#
#
#
main()