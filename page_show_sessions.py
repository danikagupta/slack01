import streamlit as st
import pandas as pd
from google.cloud import firestore

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

# Main function to display records in Streamlit
def main():
    st.title("Session Viewer")
    
    # Fetch records from Firestore collection
    collection_name = "sessions"
    records = fetch_records(collection_name)
    
    # Convert records to DataFrame
    df = pd.DataFrame(records)
    
    # Display DataFrame in Streamlit
    st.dataframe(df,
                column_config={
                'id':None
                },
                 hide_index=True, 
                 use_container_width=True)

#
#
#
main()