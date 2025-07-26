# 🎬 VideoCaptioner

**VideoCaptioner** is a subtitle assistant built with Streamlit. It helps users:
- Automatically transcribe video files into subtitles (ASR)
- Translate subtitles into multiple languages
- Preview, edit, and export subtitles (SRT format)

---

## 🚀 Features

- 🎯 **ASR Video Subtitle Recognition**: Converts speech in videos into subtitle segments.
- 🌍 **Subtitle Translation**: Supports translation to English, Chinese, Japanese, Korean, and more.
- 📝 **Subtitle Preview & Download**: View, filter, and download the SRT file.
- 🔊 Supports multiple video formats: `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, and more.

---

## 🧰 Technology Stack

- [Streamlit](https://streamlit.io/) – Interactive UI framework
- Python – Core logic & backend
- Mistral or OpenAI – For language processing / translation
- ffmpeg – Video/audio conversion

---

## 📦 Installation

```bash
git clone git@github.com:YourUsername/VideoCaptioner.git
cd VideoCaptioner
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory and define the following:

```env
# For OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1

# Or for Mistral (replace if using local inference or hosted LLM)
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_BASE_URL=https://api.mistral.ai/v1
```

Only define one (OpenAI or Mistral) depending on your backend setup.

---

## ▶️ Run the App

```bash
streamlit run streamlit_app.py
```

---

## 🌐 Supported Translations

- English
- Simplified Chinese
- Traditional Chinese
- Japanese
- Korean
- French
- German
- Spanish
- Russian
- Portuguese
- Turkish
- Cantonese

---

## 📂 Project Structure

```
VideoCaptioner/
├── app/                      # Core modules (ASR, translation, processing)
├── resource/                 # Static resources
├── streamlit_app.py          # Main Streamlit entry point
├── requirements.txt
├── .env                      # API keys (not committed)
└── README.md
```

---

## 🤝 Contributing

Pull requests are welcome! Please:
- Fork the repo
- Create a feature branch
- Commit changes
- Open a PR

---

## 📄 License

MIT License
