from google.cloud import firestore

def find_zoom_session(session_id):
    db = firestore.Client()
    doc_ref = db.collection(u'sessions').document(session_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

def fetch_sessions_with_transcripts(credentials):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'sessions')
    query = collection_ref.where('status', '==', 'transcripted')
    docs = query.stream()
    
    # Collect document IDs that match the query
    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return results
    
def fetch_document_id(credentials, url):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'sessions')
    query = collection_ref.where('youtube_url', '==', url)
    docs = query.stream()
    
    # Collect document IDs that match the query
    results = [{'id': doc.id, **doc.to_dict()} for doc in docs]
    return results

def update_session_field_by_id(credentials, document_id, field_name, new_value, new_status):
    db = firestore.Client(credentials=credentials)
    collection_ref = db.collection(u'sessions')
    
    # Reference to the specific document within the collection
    document_ref = collection_ref.document(document_id)
    
    # Update the field in the document
    document_ref.update({field_name: new_value, 'status': new_status})
    print(f"Document {document_id} updated: {field_name} = {new_value}")

    
def check_and_add_zoom_session(credentials,hash_id,title,timestamp,youtube_url):
    db = firestore.Client(credentials=credentials)
    doc_ref = db.collection(u'sessions').document(hash_id)
    doc = doc_ref.get()
    if doc.exists:
        #print(f"Session {hash_id} already exists")
        return
    else:
        #print(f"Adding session: {hash_id}")
        doc_ref.set({
            u'title': title,
            u'timestamp': timestamp,
            u'youtube_url': youtube_url,
            u'status' : 'new'
        })
        #print(f"Session {hash_id} added")
        return