import streamlit as st
import os
import json
import requests
from google.oauth2 import service_account
import vertexai
from vertexai.preview.generative_models import GenerativeModel
from google.cloud import texttospeech
from vertexai.preview.vision_models import ImageGenerationModel

# ---------------------------------------------------------
# ---------------------------------------------------------
# 1. SETUP & AUTH (Cloud Compatible ☁️)
# ---------------------------------------------------------
try:
    # Option A: Local Machine (Checks for file FIRST)
    if os.path.exists("service-account.json"):
        credentials = service_account.Credentials.from_service_account_file("service-account.json")
        with open("service-account.json") as f:
            PROJECT_ID = json.load(f)['project_id']
            
    # Option B: Streamlit Cloud (Uses Secrets)
    else:
        try:
            key_dict = st.secrets["gcp_service_account"]
            credentials = service_account.Credentials.from_service_account_info(key_dict)
            PROJECT_ID = key_dict.get("project_id", "gaslight-488509") 
        except FileNotFoundError:
            st.error("🚨 Login Failed: 'service-account.json' is missing from your active folder.")
            st.stop()

    LOCATION = "us-central1"
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)

except Exception as e:
    st.error(f"Authentication Error: {e}")
    st.stop()
# ---------------------------------------------------------
# 2. HELPER FUNCTIONS 🧠
# ---------------------------------------------------------

def get_transfers(address):
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
    try:
        response = requests.get(url) 
        data = response.json()
        return data.get('data', [])[:3] 
    except:
        return []

def analyze_wallet_vibe(tx_data):
    if not tx_data:
        return "The Ghost", "A mysterious, empty void. Silent. Dormant."
    
    # Safe float conversion
    try:
        total_volume = sum(float(t.get('value', 0)) for t in tx_data)
    except:
        total_volume = 0
        
    tx_count = len(tx_data)
    
    if total_volume > 1000000:
        return "The Whale", "Majestic, high-stakes, slow-moving. Themes of empire and power."
    elif tx_count >= 5: 
        return "The Bot", "Frantic, mechanical, lightning-fast. Themes of circuitry and neon."
    elif any(float(t.get('value', 0)) < 100 for t in tx_data):
        return "The Scavenger", "Gritty, survivalist, scraping by. Themes of rust and desperation."
    else:
        return "The Trader", "Calculated, risk-taking, sharp. Themes of markets and shadows."

def generate_image_stable(prompt):
    try:
        # User specified model
        model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        return images[0]
    except Exception as e:
        print(f"Image warning: {e}")
        return None

def speak_story(text, genre):
    try:
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        lang_code = "en-GB"
        voice_name = "en-GB-Neural2-D"

        if genre == "Cyberpunk Noir":
            lang_code = "en-US"
            voice_name = "en-US-Neural2-J"
        elif genre == "Watercolor Fairytale":
            lang_code = "en-GB"
            voice_name = "en-GB-Neural2-C"
        elif genre == "80s Anime":
            lang_code = "en-US"
            voice_name = "en-US-Neural2-F"

        voice = texttospeech.VoiceSelectionParams(language_code=lang_code, name=voice_name)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.90, 
            pitch=-1.0 
        )
        
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        # st.error(f"Audio Error: {e}") 
        return None

# ---------------------------------------------------------
# 3. UI 🎨
# ---------------------------------------------------------
st.set_page_config(page_title="Ledger Bard", page_icon="👑", layout="wide")

st.markdown("""
<style>
    .story-title { font-size: 24px; font-weight: bold; color: #FF4B4B; margin-top: 20px;}
    .story-text {
        font-family: 'Courier New', Courier, monospace;
        font-size: 16px;
        line-height: 1.6;
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ff4b4b;
        color: #FAFAFA;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Config")
    wallet_address = st.text_input("Wallet Address", "TMwFHYXLJaRUPeW6421aqXL4ZEzPRFGkGT")
    genre = st.selectbox("Genre", ["Cyberpunk Noir", "Watercolor Fairytale", "80s Anime", "Dark Fantasy"])
    st.info("💡 **Tip:** Try different genres to hear different voices!")

st.title("👑 Ledger Bard: The Creative Storyteller")
st.caption("Multimodal Narrative Generator | Vertex AI + Gemini + Google TTS")

# ---------------------------------------------------------
# 4. MAIN LOGIC 🎬
# ---------------------------------------------------------
if st.button("✨ Visualize & Narrate Wallet", type="primary"):
    
    # 1. FETCH
    with st.spinner("🔍 Scanning Blockchain..."):
        tx_data = get_transfers(wallet_address)
    
    # 2. ANALYZE
    vibe_name, vibe_desc = analyze_wallet_vibe(tx_data)
    st.success(f"🎭 **Persona:** {vibe_name}")
    
    # 3. PREPARE DATA
    last_tx_amount = 0
    if tx_data and len(tx_data) > 0:
        try:
            val = float(tx_data[0].get('value', 0))
            last_tx_amount = val / 1000000 if val > 1000 else val
            last_tx_amount = round(last_tx_amount, 2)
        except: pass

    if last_tx_amount > 5000:
        stakes = "The fate of the network."
        obj_name = "The Master Key"
    elif last_tx_amount > 100:
        stakes = "Survival."
        obj_name = "A new identity chip"
    else:
        stakes = "Just getting by."
        obj_name = "Ramen credits"

    # 4. PROMPT
    prompt = f"""
    You are a novelist.
    **GENRE:** {genre}
    **CHARACTER:** {vibe_name}
    **DATA POINTS:** Amount: {last_tx_amount}. Object: {obj_name}. Stakes: {stakes}.
    
    **TASK:** Write 3 SCENES (Setup, Climax, Ending).
    
    **FORMAT RULES:**
    - Use "SCENE [Number]: [Title]"
    - Then write the story text on the NEXT lines.
    - Then use "IMAGE_PROMPT: [Description]"
    
    **EXAMPLE OUTPUT:**
    SCENE 1: The Rain
    The rain fell hard on the neon streets. He checked his ledger.
    IMAGE_PROMPT: Dark rainy street, neon lights.
    """

    # 5. GENERATE
    # User specified model
    model = GenerativeModel("gemini-2.0-flash-lite-001")
    
    with st.spinner("🤖 Writing script..."):
        try:
            response = model.generate_content(prompt)
            full_text = response.text
        except Exception as e:
            st.error(f"Model Error: {e}")
            st.stop()

    # 6. PARSING LOOP (The Fixed Logic 🔧)
    # We collect lines until we hit an IMAGE_PROMPT
    lines = full_text.split('\n')
    
    current_title = ""
    current_text_buffer = []
    
    for line in lines:
        clean = line.strip()
        if not clean: continue
        
        # A. Detect Scene Header
        if clean.upper().startswith("SCENE"):
            # If we extract a title, just print it nicely
            current_title = clean
            st.markdown(f'<div class="story-title">{current_title}</div>', unsafe_allow_html=True)
            current_text_buffer = [] # Reset buffer for new scene text

        # B. Detect Image Prompt -> Trigger Rendering
        elif clean.upper().startswith("IMAGE_PROMPT"):
            # 1. The text collected so far is the STORY for this scene
            story_block = " ".join(current_text_buffer)
            current_text_buffer = [] # Clear immediately
            
            # Show Story
            if story_block:
                st.markdown(f'<div class="story-text">{story_block}</div>', unsafe_allow_html=True)
                
            # 2. Extract Prompt & Generate Image
            raw_prompt = clean.split(":", 1)[1].strip() if ":" in clean else clean
            final_prompt = f"{genre} style. {raw_prompt}, 8k, cinematic"
            
            with st.spinner(f"🎨 Rendering {current_title}..."):
                # Layout: Image Left, Audio Right
                col1, col2 = st.columns([2, 1])
                
                # Image
                img = generate_image_stable(final_prompt)
                with col1:
                    if img: st.image(img._image_bytes, use_container_width=True)
                
                # Audio (Reads the story block we just printed)
                with col2:
                    if story_block:
                        st.caption("🎧 Audio Narrative")
                        audio_data = speak_story(story_block, genre)
                        if audio_data:
                            st.audio(audio_data, format="audio/wav")

        # C. It is Story Text
        else:
            # Just accumulate it into the buffer
            current_text_buffer.append(clean)