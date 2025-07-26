import logging
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.core.bk_asr.asr_data import ASRData
from app.core.bk_asr.bcut import BcutASR
from app.core.subtitle_processor.optimize import SubtitleOptimizer
from app.core.subtitle_processor.translate import TranslatorFactory, TranslatorType
from app.core.utils.video_utils import video2audio

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Set environment variables with fallback if not set
os.environ["OPENAI_BASE_URL"] = os.getenv("OPENAI_BASE_URL", "")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Streamlit page config
st.set_page_config(
    page_title="Kaka Subtitle Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

def create_temp_dir():
    """Create a temporary directory for processing files."""
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    return temp_dir

def format_time(milliseconds):
    """Convert milliseconds to hh:mm:ss.mmm or mm:ss.mmm format."""
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    ms = int((total_seconds * 1000) % 1000)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d}.{ms:03d}"

def format_duration(milliseconds):
    """Format milliseconds into a readable duration string."""
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def asr_page():
    st.title("🎯 ASR Video Subtitle Recognition")
    st.markdown("---")

    # Initialize session state variables
    if "srt_content" not in st.session_state:
        st.session_state.srt_content = None
    if "subtitle_path" not in st.session_state:
        st.session_state.subtitle_path = None
    if "asr_data" not in st.session_state:
        st.session_state.asr_data = None
    if "translated_asr_data" not in st.session_state:
        st.session_state.translated_asr_data = None

    temp_dir = create_temp_dir()

    # Two column layout: Video preview | Controls
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 📺 Video Preview")
        video_file = st.file_uploader(
            label="Upload Video File",
            type=["mp4", "mov", "avi", "mkv", "flv"],
            key="asr_video",
            accept_multiple_files=False,
            label_visibility="collapsed",
            help="Supported video formats: MP4, MOV, AVI, MKV, WMV, FLV, WebM, M4V",
        )
        video_placeholder = st.empty()

        if video_file:
            video_path = temp_dir / video_file.name
            if not video_path.exists():
                with open(video_path, "wb") as f:
                    f.write(video_file.getbuffer())
                logger.info(f"Saved video file to: {video_path}")

            video_placeholder.video(
                video_file,
                subtitles=(
                    st.session_state.subtitle_path
                    if st.session_state.subtitle_path
                    else None
                ),
            )

    with col2:
        st.markdown("### 🎯 Control Panel")
        if video_file is not None:
            st.success("✅ Video uploaded successfully!")

            if st.button("🚀 Start Recognition", use_container_width=True):
                with st.spinner("⏳ Processing..."):
                    try:
                        logger.info(f"Processing video file: {video_file.name}")
                        # Convert video to audio
                        audio_path = temp_dir / f"{video_path.stem}.wav"
                        logger.info(f"Converting video to audio: {audio_path}")
                        is_success = video2audio(str(video_path), str(audio_path))

                        if not is_success:
                            logger.error("Audio conversion failed")
                            st.error("Audio conversion failed")
                            return

                        logger.info("Starting ASR recognition")
                        # Perform ASR recognition
                        asr = BcutASR(str(audio_path))
                        asr_data = asr.run()
                        logger.info("ASR recognition completed")

                        st.session_state.srt_content = asr_data.to_srt()
                        st.session_state.asr_data = asr_data

                        # Save subtitle file
                        subtitle_path = temp_dir / f"{video_path.stem}.srt"
                        logger.info(f"Saving subtitle file to: {subtitle_path}")
                        with open(subtitle_path, "w", encoding="utf-8") as f:
                            f.write(st.session_state.srt_content)

                        st.session_state.subtitle_path = str(subtitle_path)

                        # Update video display with subtitles
                        video_placeholder.video(
                            video_file, subtitles=st.session_state.subtitle_path
                        )

                        logger.info("Subtitle recognition process completed")
                        st.success("✨ Recognition completed!")

                        # Show subtitle statistics
                        if st.session_state.asr_data:
                            st.markdown("### 📊 Subtitle Statistics")
                            segments = st.session_state.asr_data.segments
                            total_segments = len(segments)
                            total_duration = sum(
                                seg.end_time - seg.start_time for seg in segments
                            )
                            total_chars = sum(len(seg.text.strip()) for seg in segments)
                            avg_segment_duration = (
                                total_duration / total_segments if total_segments > 0 else 0
                            )

                            col_stats1, col_stats2, col_stats3 = st.columns(3)
                            with col_stats1:
                                st.metric("Subtitle Segments", f"{total_segments}")
                            with col_stats2:
                                st.metric("Total Duration", format_duration(total_duration))
                            with col_stats3:
                                st.metric("Total Characters", f"{total_chars}")

                    except Exception as e:
                        logger.exception(f"Error during processing: {str(e)}")
                        st.error(f"Error during processing: {str(e)}")
                    finally:
                        # Clean up audio file
                        if "audio_path" in locals() and audio_path.exists():
                            logger.info(f"Removing temporary audio file: {audio_path}")
                            os.remove(audio_path)

            # If subtitles exist, show preview and download options
            if st.session_state.srt_content and st.session_state.asr_data:
                st.markdown("---")
                with st.expander("📝 Subtitle Preview", expanded=True):
                    search_term = st.text_input(
                        "🔍 Search subtitles",
                        key="subtitle_search",
                        placeholder="Enter keyword to search...",
                    )

                    segments = st.session_state.asr_data.segments
                    df = pd.DataFrame(
                        [
                            {
                                "Index": i + 1,
                                "Start Time": format_time(seg.start_time),
                                "End Time": format_time(seg.end_time),
                                "Duration (s)": round(
                                    (seg.end_time - seg.start_time) / 1000, 1
                                ),
                                "Subtitle Text": seg.text.strip(),
                            }
                            for i, seg in enumerate(segments)
                        ]
                    )

                    if search_term:
                        df = df[
                            df["Subtitle Text"].str.contains(
                                search_term, case=False, na=False
                            )
                        ]

                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=400,
                        hide_index=True,
                        column_config={
                            "Index": st.column_config.NumberColumn(
                                "Index", help="Subtitle segment index", format="%d", width="small"
                            ),
                            "Start Time": st.column_config.TextColumn(
                                "Start Time", help="Subtitle start time", width="small"
                            ),
                            "End Time": st.column_config.TextColumn(
                                "End Time", help="Subtitle end time", width="small"
                            ),
                            "Duration (s)": st.column_config.NumberColumn(
                                "Duration (s)", help="Subtitle duration", format="%.1f", width="small"
                            ),
                            "Subtitle Text": st.column_config.TextColumn(
                                "Subtitle Text", help="Recognized subtitle text", width="medium"
                            ),
                        },
                    )

                st.markdown("### 💾 Export Subtitles")
                st.download_button(
                    label="📥 Download SRT Subtitle File",
                    data=st.session_state.srt_content,
                    file_name=f"{video_file.name.rsplit('.', 1)[0]}.srt",
                    mime="text/plain",
                    use_container_width=True,
                )


def translation_page():
    st.title("🌏 Subtitle Translation")
    st.markdown("---")

    # Initialize session state variables
    if "translated_content" not in st.session_state:
        st.session_state.translated_content = None
    if "current_subtitle_file" not in st.session_state:
        st.session_state.current_subtitle_file = None
    if "translation_done" not in st.session_state:
        st.session_state.translation_done = False

    temp_dir = create_temp_dir()

    with st.container():
        subtitle_file = st.file_uploader(
            label="Upload Subtitle File",
            type=["srt", "ass", "vtt"],
            key="trans_subtitle",
            label_visibility="visible",
            help="Supports SRT, ASS, VTT subtitle formats",
        )

        target_language = st.selectbox(
            "Select Target Language for Translation",
            [
                "English",
                "Simplified Chinese",
                "Traditional Chinese",
                "Japanese",
                "Korean",
                "Cantonese",
                "French",
                "German",
                "Spanish",
                "Russian",
                "Portuguese",
                "Turkish",
            ],
            index=0,
            help="Select the language to translate subtitles into",
        )

    if (
        subtitle_file is not None
        and subtitle_file != st.session_state.current_subtitle_file
    ):
        if st.session_state.current_subtitle_file:
            old_path = temp_dir / st.session_state.current_subtitle_file.name
            if os.path.exists(old_path):
                os.remove(old_path)
        st.session_state.current_subtitle_file = subtitle_file
        st.session_state.translation_done = False
        st.session_state.translated_content = None
        st.session_state.translated_asr_data = None

    if subtitle_file is not None:
        subtitle_path = temp_dir / subtitle_file.name
        with open(subtitle_path, "wb") as f:
            f.write(subtitle_file.getbuffer())

        # Show original subtitle preview
        with st.expander("Original Subtitle Preview"):
            asr_data = ASRData.from_subtitle_file(str(subtitle_path))
            st.session_state.asr_data = asr_data
            subtitle_json = st.session_state.asr_data.to_json()
            df = pd.DataFrame(
                [
                    {
                        "Start Time": format_time(v["start_time"]),
                        "End Time": format_time(v["end_time"]),
                        "Original": v["original_subtitle"],
                        "Translation": v["translated_subtitle"],
                    }
                    for k, v in subtitle_json.items()
                ]
            )
            st.dataframe(df, use_container_width=True)

        if st.button("Start Translation", use_container_width=True):
            with st.spinner("Translating..."):
                try:
                    logger.info(f"Translating subtitle file: {subtitle_file.name}")
                    asr_data = ASRData.from_subtitle_file(str(subtitle_path))

                    logger.info(f"Target language: {target_language}")
                    translator = TranslatorFactory.create_translator(
                        translator_type=TranslatorType.BING,
                        target_language=target_language,
                    )

                    subtitle_json = {
                        str(k): v["original_subtitle"]
                        for k, v in asr_data.to_json().items()
                    }
                    logger.info(f"Number of subtitle segments to translate: {len(subtitle_json)}")

                    asr_data = translator.translate_subtitle(asr_data)
                    logger.info("Translation completed")

                    st.session_state.translated_content = asr_data.to_srt()
                    st.session_state.translated_asr_data = asr_data
                    st.session_state.translation_done = True

                    logger.info("Subtitle translation process completed")
                    st.success("Translation completed!")

                except Exception as e:
                    logger.exception(f"Error during translation: {str(e)}")
                    st.error(f"Error during translation: {str(e)}")

        if (
            st.session_state.translation_done
            and st.session_state.translated_asr_data is not None
        ):
            st.subheader("Translation Preview")
            subtitle_json = st.session_state.translated_asr_data.to_json()
            df = pd.DataFrame(
                [
                    {
                        "Start Time": format_time(v["start_time"]),
                        "End Time": format_time(v["end_time"]),
                        "Original": v["original_subtitle"],
                        "Translation": v["translated_subtitle"],
                    }
                    for k, v in subtitle_json.items()
                ]
            )
            st.dataframe(df, use_container_width=True)

            st.markdown("### 💾 Download Translated Subtitle File")
            st.download_button(
                label="📥 Download Translated SRT File",
                data=st.session_state.translated_content,
                file_name=f"{subtitle_file.name.rsplit('.', 1)[0]}_translated.srt",
                mime="text/plain",
                use_container_width=True,
            )


def main():
    st.sidebar.title("Kaka Subtitle Assistant")
    app_mode = st.sidebar.radio(
        "Select Mode", ["Subtitle Recognition (ASR)", "Subtitle Translation"]
    )

    if app_mode == "Subtitle Recognition (ASR)":
        asr_page()
    elif app_mode == "Subtitle Translation":
        translation_page()


if __name__ == "__main__":
    main()
