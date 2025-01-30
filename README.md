# StreamBuzz 🚀

---

## **Your AI-powered YouTube Live Stream Chat Moderator**

**Attention Streamers!!**

Tired of drowning in a tsunami of chat messages while trying to present to your audience? StreamBuzz to the rescue! This AI sidekick filters key messages, handles FAQs, and posts replies—so you can focus on being the rockstar streamer you were born to be.

---

## **Why StreamBuzz?**

Live streaming is booming, with over **2 billion monthly YouTube users**. Streamers educate, entertain, and engage, but juggling an avalanche of chat messages **while presenting** is like trying to play chess on a roller coaster. 🎢 Important questions, concerns, and requests get lost in the flood, making chat management feel impossible.

### **The Solution**

StreamBuzz **filters the noise, highlights key messages, and automates replies**, so you can engage without stress. No more hunting through chat chaos—just smooth sailing! ⛵

<p align="center">
  <img src="./media/demo.gif" width="70%" alt="StreamBuzz Live Demo">
</p>
<p align="center"><b>Watch how StreamBuzz moderates live chats effortlessly!</b></p>


### **Benefits**

**🎯 Focus on Content** – Let StreamBuzz handle chat while you do your thing.\
**🔍 Better Engagement** – Important questions, concerns, and requests **stand out**.\
**⏳ Saves Time** – Generates replies for buzz (important messages), reducing your mental load.\
**🛠️ Customizable** – Update your knowledge base, and StreamBuzz **adapts automatically**.\
**💬 Improves Viewer Experience** – Ensures timely, relevant, typo-free responses.

---

### **Usage**

1️⃣ Start a YouTube Live Stream.\
2️⃣ StreamBuzz filters and prioritizes chat messages (buzz) in the background.\
3️⃣ Navigate through the **real-time buzz list** like a pro.\
4️⃣ Post replies **directly from the chat interface**—error-free and neatly summarized. StreamBuzz background worker takes care of summarizing and posting your replies. \
5️⃣ Upload a text file to build a knowledge base and supercharge your responses. ⚡

All in all, StreamBuzz is the ultimate **companion and chat moderator** for YouTube Live Streamers. Think of it as your chat butler. ☕

---

### **Features**

🔹 **AI Chat Moderation** – Extracts key messages (buzz) from an ocean of chat spam. Navigate buzz at your own pace.\
🔹 **Suggested Replies** – Auto-generates responses and allows customization via a text-based knowledge base.\
🔹 **RAG (Retrieval-Augmented Generation)** – Smarter responses for streamers and chat queries.\
🔹 **Seamless YouTube Integration** – Works directly with YouTube Live Chat **in real time**.

---

## **Getting Started**

### **Installation**

```bash
# Clone the repository
git clone https://github.com/hammaadworks/streambuzz.git
cd streambuzz

# Create a virtual environment (optional)
python -m venv .venv
source ./.venv/bin/activate

# Install dependencies
pip install -Ur requirements.txt
```

Alternatively, build an image from the `Dockerfile` and save yourself the setup hassle.

### **Configuration**

1. Fill in your keys as specified in the `.env.example` file. Use your model of choice by changing variables in `constants.py` under model section.
2. Create database tables using the DDL commands provided in `queries.sql` file. This project uses Supabase. You can store your YouTube API keys in the `youtube_keys` table.

    *Note: Hackathon organisers kindly contact [me](mailto:hammaadworks@gmail.com) for Supabase domain and anon key or kindly share those, I'll add the YouTube keys*
    
3. Set up the user interface using **Agent 0 by Ottomator.ai** ([Agent 0](https://studio.ottomator.ai/agent/0)).


### **Running StreamBuzz**
1. Set Environment Variable in `.env` file

    ```bash
    # Copy .env.example to .env and set your keys in .env file
    cp .env.example .env
    ```

2. Serve the FastAPI app

    ```bash
    fastapi-cli dev streambuzz.py --port 8001 --reload
    ```

    Alternatively, you can use `uvicorn`:

    ```bash
    uvicorn streambuzz:app --host 0.0.0.0 --port 8001
    ```

---

## **Demo & Architecture**

### **Demo Gallery 🎥**

#### **Experience StreamBuzz in Action!**

## **Watch StreamBuzz in Action!** 🎬  

<p align="center">
  <a href="https://www.youtube.com/watch?v=YOUR_VIDEO_ID">
    <img src="https://img.youtube.com/vi/YOUR_VIDEO_ID/maxresdefault.jpg" alt="StreamBuzz Demo" width="600">
  </a>
</p>

<p align="center"><b>0. Click the thumbnail to watch the demo on YouTube! 🚀</b></p>

<p align="center">
  <img src="./media/start_stream.png" width="60%" alt="Start Chat Moderation">
</p>
<p align="center"><b>1. Start chat moderation with ease.</b></p>


<p align="center">
  <img src="./media/chat_nav.png" width="60%" alt="Chat Navigation">
</p>
<p align="center"><b>2. Navigate through chat messages effortlessly.</b></p>


<p align="center">
  <img src="./media/caught-up.png" width="60%" alt="Caught Up">
</p>
<p align="center"><b>3. Stay up to date with all key chats. 🎉</b></p>


<p align="center">
  <img src="./media/reply.png" width="60%" alt="Reply Integration">
</p>
<p align="center"><b>4. Seamless reply integration with YouTube Live Chat.</b></p>


<p align="center">
  <img src="./media/post_reply.png" width="60%" alt="YouTube Reply">
</p>
<p align="center"><b>5. Replies posted within a timeframe of 60 seconds on YouTube Live Chat.</b>
</p>


### **Architecture Diagrams**

<p align="center">
  <img src="./media/agents.png" width="70%" alt="StreamBuzz Live Demo">
</p>
<p align="center"><b>A Moderator Crew of 4 Agents to your rescue!</b></p>

---

## **Acknowledgments**  

StreamBuzz was created as part of the **oTTomator Live Agent Studio Hackathon**.  
Huge shoutout to [**Cole Medin**](https://github.com/coleam00) and the [**Ottomator AI Team**](https://studio.ottomator.ai/)  
for hosting this incredible event and pushing the boundaries of AI-powered automation! 🎉  

A massive thank you to the **open-source community** for their contributions, making cutting-edge technology accessible to all.  
Special appreciation for projects like **[Pydantic AI](https://ai.pydantic.dev/)** and others, 
your work makes innovations like StreamBuzz possible!  

To all **content creators** who educate, share knowledge, and make resources more accessible—you are shaping the future!  
Special mentions go to:  

- 🎥 [**Cole Medin**](https://www.youtube.com/@ColeMedin) – Breaking down AI, automation, and building cool stuff.  
- 🎥 [**Your Tech Bud Codes**](https://www.youtube.com/@YourTechBudCodes) – Making tech & coding easier for everyone.  

---

### **Special Thanks to the Global Streamer Community** 🎙️✨  

Most importantly, **a heartfelt thanks to the global streamer community**—the educators, entertainers, and innovators  
who make live streaming a hub of knowledge and engagement.  

You inspire us to build tools that make your work easier and your content even better.  
**This is for you!** 🚀

---
