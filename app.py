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
# 1. SETUP & AUTH (Cloud Compatible ☁️)
# ---------------------------------------------------------
try:
    # Option A: Streamlit Cloud (Secrets)
    if "gcp_service_account" in st.secrets:
        key_dict = st.secrets["gcp_service_account"]
        credentials = service_account.Credentials.from_service_account_info(key_dict)
        PROJECT_ID = key_dict.get("project_id", "gaslight-488509") 
    
    # Option B: Local Machine (File)
    elif os.path.exists("service-account.json"):
        credentials = service_account.Credentials.from_service_account_file("service-account.json")
        with open("service-account.json") as f:
            PROJECT_ID = json.load(f)['project_id']
            
    else:
        st.error("🚨 Login Failed: No 'service-account.json' found and no Secrets detected.")
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
    """Fetches real transaction data (TRON) or returns mock data on failure."""
    url = f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20"
    try:
        response = requests.get(url) 
        data = response.json()
        return data.get('data', [])[:3]  # Return top 3 tx
    except:
        return [] # Return empty if API fails

def analyze_wallet_vibe(tx_data):
    """Determines the personality of the wallet based on data."""
    if not tx_data:
        return "The Ghost", "A mysterious, empty void where echoes of the past linger. Silent. Dormant."
    
    total_volume = sum(float(t.get('value', 0)) for t in tx_data)
    tx_count = len(tx_data)
    
    # Logic to determine "Vibe"
    if total_volume > 1000000:
        return "The Whale", "Majestic, high-stakes, slow-moving but impactful. Themes of empire, luxury, and power."
    elif tx_count >= 5: 
        return "The Bot", "Frantic, mechanical, lightning-fast. Themes of circuitry, data overload, and neon."
    elif any(float(t.get('value', 0)) < 100 for t in tx_data):
        return "The Scavenger", "Gritty, survivalist, scraping by in the Rain District. Themes of rust and desperation."
    else:
        return "The Trader", "Calculated, risk-taking, sharp. Themes of markets, charts, and shadows."

def generate_image_stable(prompt):
    """Generates an image using Vertex AI Imagen."""
    try:
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
        print(f"Image Error: {e}")
        return None

def speak_story(text, genre):
    """Generates audio using Google Cloud TTS with Dynamic Voices."""
    try:
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # 🎭 Dynamic Voice Selection based on Genre
        # Default: British Bard
        lang_code = "en-GB"
        voice_name = "en-GB-Neural2-D" # Deep British Male

        if genre == "Cyberpunk Noir":
            lang_code = "en-US"
            voice_name = "en-US-Neural2-J" # Deep/Gritty American Male
        elif genre == "Watercolor Fairytale":
            lang_code = "en-GB"
            voice_name = "en-GB-Neural2-C" # Soft Female
        elif genre == "80s Anime":
            lang_code = "en-US"
            voice_name = "en-US-Neural2-F" # Energetic Female

        voice = texttospeech.VoiceSelectionParams(
            language_code=lang_code, 
            name=voice_name
        )
        
        # 🔊 Use WAV (Linear16) for Safari/Chrome compatibility
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=0.90, # Slightly slower for storytelling
            pitch=2.0 # Slightly higher pitch for more emotion
        )
        
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
        
    except Exception as e:
        st.error(f"Audio Error: {e}")
        return None

# ---------------------------------------------------------
# 3. UI & APP LOGIC 🎨
# ---------------------------------------------------------

st.set_page_config(page_title="Ledger Bard", page_icon="👑", layout="wide")

# Custom CSS for cinematic look
st.markdown("""
<style>
    .story-text {
        font-family: 'Courier New', Courier, monospace;
        font-size: 18px;
        line-height: 1.6;
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
        color: #e0e0e0;
    }
    .stApp { background-color: #0e1117; }
</style>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.header("Config")
    wallet_address = st.text_input("Wallet Address", "TMw... (Enter TRON Address)")
    genre = st.selectbox("Genre", ["Cyberpunk Noir", "Watercolor Fairytale", "80s Anime", "Dark Fantasy"])
    
    st.divider()
    st.info("💡 **Tip:** Try different genres to hear different voices!")

st.title("👑 Ledger Bard: The Creative Storyteller")
st.caption("Multimodal Narrative Generator | Vertex AI + Gemini + Google TTS")

if st.button("✨ Visualize & Narrate Wallet", type="primary"):
    
    # 1. Fetch Data
    with st.spinner("🔍 Scanning Blockchain..."):
        tx_data = get_transfers(wallet_address)
    
    # 2. Analyze Persona (The "Brain")
    vibe_name, vibe_desc = analyze_wallet_vibe(tx_data)
    st.success(f"🎭 **Persona Detected:** {vibe_name}")
    st.caption(f"_{vibe_desc}_")
    
    # 3. Prompt Engineering (The "Creative Director")
    # ... inside the button click ...

# ... inside the button click event ...

    # 1. Extract Specific Planning Data to force consistency
    # (We use the actual data to ground the story)
    last_tx_amount = float(tx_data[0].get('value', 0)) if tx_data else 0
    tx_type = "Transfer" # Placeholder, could be 'Mint' or 'Burn' if you had that data
    
    # 2. Define the "Stakes" based on value
    if last_tx_amount > 10000:
        stakes = "The fate of the entire network is at risk."
        object_of_desire = "The Golden Key code"
    elif last_tx_amount > 100:
        stakes = "Survival. Payment for a new identity."
        object_of_desire = "Clean passports"
    else:
        stakes = "Desperation. Just enough for a meal and a recharge."
        object_of_desire = "A bowl of synthetic ramen"

    # 3. 🧠 THE ULTIMATE "DEEP DIVE" PROMPT
    prompt = f"""
    You are an award-winning novelist and cinema director known for gritty, visceral detail.
    
    **THE SETTING:**
    Genre: {genre} (Strictly adhere to this visual style).
    Character Function: {vibe_name} ({vibe_desc}).
    
    **THE "HARD DATA" PLOT POINTS (You MUST use these):**
    1. The exact currency amount involved is: **{last_tx_amount} units**.
    2. The stakes are: **{stakes}**.
    3. The object being bought/sold is: **{object_of_desire}**.
    
    **WRITING RULES (CRITICAL):**
    - **NO GENERALITIES.** Don't say "he paid the money." Say "He slid the credit chip across the wet chrome table. It blinked '{last_tx_amount}' in red light."
    - **SENSORY DETAILS:** Describe smells (ozone, rain, rust), sounds (humming servers, distinct footsteps), and textures.
    - **SHOW, DON'T TELL.**
    
    **GENERATE 3 SCENES (Beginning, Climax, Aftermath):**
    
    SCENE 1 (THE ATMOSPHERE):
    [Set the scene. Where is the character? What are they waiting for? Describe the environment with intense detail. Establish the `{vibe_name}` persona.]
    IMAGE_PROMPT 1:
    [{genre} style. Wide angle. establishing shot. Focusing on lighting, atmosphere, and the scale of the world. Cinematic 8k.]
    
    SCENE 2 (THE TRANSACTION - CLIMAX):
    [The exchange happens. Verification. The tension peaks. The specific amount **{last_tx_amount}** must appear on a screen or interface. betrayal? Success?]
    IMAGE_PROMPT 2:
    [{genre} style. Macro close-up. Hands exchanging a digital drive or device. The number '{last_tx_amount}' glowing on a screen. High contrast. Depth of field.]
    
    SCENE 3 (THE CONSEQUENCE - ENDING):
    [The immediate aftermath. The character escapes or disappears. A definitive ending to this chapter. The screen fades to black.]
    IMAGE_PROMPT 3:
    [{genre} style. Low angle. The character walking away into the distance/fog/light. Text "TRANSACTION COMPLETE" floating in the air holographic style.]
    """

    model = GenerativeModel("gemini-2.0-flash-lite-001")
    
    with st.spinner("🤖 Dreaming up the narrative..."):
        response = model.generate_content(prompt)
        full_text = response.text

    # 4. Parsing & Generation Loop
    lines = full_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Clean markdown formatting just in case
        clean_line = line.replace("**", "").replace("##", "").strip()
        
        if not clean_line: continue
        
        # Detect SCENE (Text + Audio)
        if clean_line.upper().startswith("SCENE"):
            display_text = clean_line.split(":", 1)[1].strip() if ":" in clean_line else clean_line
            
            st.markdown(f"### {clean_line.split(':')[0]}") 
            st.markdown(f'<div class="story-text">{display_text}</div>', unsafe_allow_html=True)
            
            # Generate Audio (wav)
            audio_bytes = speak_story(display_text, genre)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")

        # ... inside the loop ...

        # Detect IMAGE (Visuals)
        elif clean_line.upper().startswith("IMAGE_PROMPT"):
            raw_prompt = clean_line.split(":", 1)[1].strip() if ":" in clean_line else clean_line
            # Inject the Persona into the visual prompt to make it unique
            final_prompt = f"{genre} style. {vibe_name} character. {raw_prompt}, cinematic lighting, 8k"
            
            with st.spinner(f"🎨 Painting scene..."):
                img = generate_image_stable(final_prompt)
                if img:
                    # ✨ COMIC BOOK LAYOUT ✨
                    # Image on Left (2 parts), Story/Audio on Right (1 part)
                    col1, col2 = st.columns([2, 1]) 
                    
                    with col1:
                        st.image(img._image_bytes, use_container_width=True)
                    
                    with col2:
                        st.caption(f"Visual: {raw_prompt[:50]}...")
                        # We move the audio player here so it sits next to the image
                        if 'last_audio' in st.session_state:
                             st.audio(st.session_state.last_audio, format="audio/wav")