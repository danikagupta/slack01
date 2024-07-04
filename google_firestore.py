from google.cloud import firestore

def find_zoom_session(session_id):
    db = firestore.Client()
    doc_ref = db.collection(u'sessions').document(session_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None
    
def check_and_add_zoom_session(credentials,hash_id,title,timestamp,youtube_url):
    db = firestore.Client(credentials=credentials)
    doc_ref = db.collection(u'sessions').document(hash_id)
    doc = doc_ref.get()
    if doc.exists:
        print(f"Session {hash_id} already exists")
        return
    else:
        print(f"Adding session: {hash_id}")
        doc_ref.set({
            u'title': title,
            u'timestamp': timestamp,
            u'youtube_url': youtube_url
        })
        print(f"Session {hash_id} added")
        return