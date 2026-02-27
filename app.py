import streamlit as st
import os
import requests
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from vertexai.preview.vision_models import ImageGenerationModel
from google.cloud import texttospeech

# ---------------------------------------------------------
# 1. SETUP & AUTH (Must be at the top) 🛠️
# ---------------------------------------------------------
key_path = "service-account.json" 
credentials = service_account.Credentials.from_service_account_file(key_path)

with open(key_path) as f:
    key_data = json.load(f)
    PROJECT_ID = key_data['project_id']

LOCATION = "us-central1" # Or us-east1 if central fails

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

# ---------------------------------------------------------
# 2. AUDIO FUNCTION (The Bard's Voice) 🗣️
# ---------------------------------------------------------
def speak_story(text):
    try:
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # ... inside speak_story ...
    
        # ✅ PREMIUM VOICE: "The British Bard"
        # (Much more expressive and deep)
        voice = texttospeech.VoiceSelectionParams(
        language_code="en-GB", 
        name="en-GB-Neural2-D" 
       )
    
       # Switch back to MP3 (Chrome handles it fine and it sounds better)
        audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # ... rest of function ...
        
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
        
    except Exception as e:
        # ✅ SHOW THE ERROR ON SCREEN
        st.error(f"Audio Error: {e}")
        return None

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------
def get_tron_data(address):
    url = f"https://apilist.tronscan.org/api/transaction?sort=-timestamp&count=true&limit=3&start=0&address={address}"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        simplified_txs = []
        for tx in data.get('data', []):
            simplified_txs.append({
                "hash": tx.get('hash', '???')[:8] + "...",
                "amount": tx.get('amount', 0),
                "token": tx.get('tokenInfo', {}).get('tokenAbbr', 'TRX')
            })
        return simplified_txs
    except:
        return []

def generate_image_stable(prompt_text):
    try:
        # Using Imagen 3
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")
        images = model.generate_images(
            prompt=prompt_text,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some", 
            person_generation="allow_adult" 
        )
        return images[0]
    except Exception as e:
        print(f"Image Error: {e}")
        return None

# ---------------------------------------------------------
# 4. THE UI & STYLING
# ---------------------------------------------------------
st.set_page_config(page_title="Ledger Bard", page_icon="📜", layout="centered")

# CSS Styling
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    .stTextInput > div > div > input { background-color: #262730; color: #FAFAFA; border-radius: 10px; }
    .stButton > button {
        background: linear-gradient(45deg, #FF4B4B, #FF914D);
        color: white; border: none; border-radius: 25px; height: 50px; width: 100%;
        font-size: 20px; font-weight: bold;
    }
    .story-text {
        font-family: 'Courier New', Courier, monospace;
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        line-height: 1.6;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📜 The Ledger Bard")
st.caption(f"Connected to: {PROJECT_ID}")

with st.sidebar:
    st.header("Config")
    target_address = st.text_input("Wallet Address", "TMwFHYXLJaRUPeW6421aqXL4ZEzPRFGkGT")
    genre = st.selectbox("Genre", ["Cyberpunk Noir", "Watercolor Fairytale", "80s Anime", "Oil Painting"])

if st.button("✨ Visualize this Wallet"):
    
    # 1. Get Data
    with st.spinner("📡 Intercepting Blockchain Data..."):
        tx_data = get_tron_data(target_address)
        if not tx_data:
            st.warning("No transactions found! Using simulation data.")
            tx_data = [{"amount": 1000, "token": "TRX"}, {"amount": 500, "token": "USDT"}]

    # 2. Generate Story Plan
    prompt = f"""
    You are a visual storyteller.
    Context: The user is looking at these crypto transactions: {json.dumps(tx_data)}
    Style: {genre}

    Create a 3-part micro-story.
    Format your response EXACTLY like this:
    
    SCENE 1: [Write 2 sentences of story here]
    IMAGE_PROMPT 1: [Detailed visual description of Scene 1, no text in image]
    
    SCENE 2: [Write 2 sentences of story here]
    IMAGE_PROMPT 2: [Detailed visual description of Scene 2, no text in image]
    
    SCENE 3: [Write 2 sentences of story here]
    IMAGE_PROMPT 3: [Detailed visual description of Scene 3, no text in image]
    """

    with st.spinner("🧠 Writing story with Gemini..."):
        try:
            model = GenerativeModel("gemini-2.0-flash-lite-001")
            response = model.generate_content(prompt)
            full_text = response.text
        except Exception as e:
            st.error(f"Text Gen Error: {e}")
            st.stop()
        
    # ---------------------------------------------------------
    # 3. ROBUST PARSING & AUDIO 🎧
    # ---------------------------------------------------------
    lines = full_text.split('\n')
    
    current_scene_text = ""
    
    for line in lines:
        line = line.strip()
        # Remove markdown bolding just in case (**SCENE 1** -> SCENE 1)
        clean_line = line.replace("**", "").replace("##", "").strip()
        
        if not clean_line: continue
        
        # Smat matching for "SCENE" (Case insensitive)
        if clean_line.upper().startswith("SCENE"):
            
            # Extract just the story text (Remove "SCENE 1:" part)
            if ":" in clean_line:
                display_text = clean_line.split(":", 1)[1].strip()
            else:
                display_text = clean_line
            
            # 1. Show Text
            st.markdown(f"### {clean_line.split(':')[0]}") 
            st.markdown(f'<div class="story-text">{display_text}</div>', unsafe_allow_html=True)
            
            # 2. Speak Text
            if display_text:
                with st.spinner("🔊 Generating Audio..."):
                    audio_bytes = speak_story(display_text)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3")
                    else:
                        st.error("Audio generation failed. Check terminal for error.")
            
        elif clean_line.upper().startswith("IMAGE_PROMPT"):
            # Extract prompt
            if ":" in clean_line:
                raw_prompt = clean_line.split(":", 1)[1].strip()
            else:
                raw_prompt = clean_line
                
            final_prompt = f"{genre} style. {raw_prompt}"
            
            with st.spinner(f"🎨 Painting..."):
                img = generate_image_stable(final_prompt)
                if img:
                    st.image(img._image_bytes, use_container_width=True)
