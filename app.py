import streamlit as st
import yt_dlp
import tempfile
import os
import zipfile
import io

st.set_page_config(page_title="YouTube Downloader", page_icon="🎬")
st.title("🎬 YouTube Playlist / Single Video Downloader")
st.write(
    "Paste a playlist or single video URL, choose your format, and get all files "
    "in one ZIP archive."
)

playlist_url = st.text_input("Playlist or Video URL")

format_choice = st.radio(
    "Choose output format:",
    ("MP3 Audio", "MP4 Video (1080p)"),
    index=0,
    help="MP3: best audio quality (192 kbps). Video: best 1080p MP4 with audio."
)

if "downloading" not in st.session_state:
    st.session_state.downloading = False
if "zip_data" not in st.session_state:
    st.session_state.zip_data = None

def start_download():
    if not playlist_url:
        st.warning("Please enter a URL first.")
        return

    if st.session_state.downloading:
        st.warning("A download is already in progress. Please wait.")
        return

    st.session_state.downloading = True
    st.session_state.zip_data = None

    if format_choice == "MP3 Audio":
        file_ext = "mp3"
        download_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "ignoreerrors": True,
            "nooverwrites": True,
            "quiet": True,
        }
    else:
        file_ext = "mp4"
        download_opts = {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "merge_output_format": "mp4",
            "ignoreerrors": True,
            "nooverwrites": True,
            "quiet": True,
        }

    try:
        with st.spinner("Processing... this may take a while depending on the size."):
            flat_opts = {"extract_flat": True, "quiet": True}
            with yt_dlp.YoutubeDL(flat_opts) as ydl_flat:
                info = ydl_flat.extract_info(playlist_url, download=False)

            entries = info.get("entries")
            if entries:
                entries = [e for e in entries if e]
            else:
                entries = [info]

            if not entries:
                st.error("No videos found. Check the URL.")
                return

            total = len(entries)
            st.write(f"Found **{total}** video(s). Starting download...")

            progress_bar = st.progress(0)
            status_text = st.empty()

            with tempfile.TemporaryDirectory() as tmpdir:
                download_opts["outtmpl"] = os.path.join(tmpdir, f"%(title)s.{file_ext}")

                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    for i, entry in enumerate(entries):
                        if entry is None:
                            continue

                        video_url = entry.get("webpage_url") or entry.get("url") or playlist_url
                        if not video_url:
                            continue

                        status_text.text(
                            f"Downloading ({i + 1}/{total}): {entry.get('title', 'Unknown')}"
                        )

                        try:
                            ydl.download([video_url])
                        except Exception as e:
                            st.error(f"Failed: `{entry.get('title', 'Unknown')}` – {e}")

                        progress_bar.progress((i + 1) / total)

                status_text.text("Creating ZIP archive...")
                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(tmpdir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, tmpdir)
                            zf.write(file_path, arcname)

                zip_buffer.seek(0)
                st.session_state.zip_data = zip_buffer.getvalue()

            status_text.text("✅ Done! Click the button below to download your ZIP.")
            progress_bar.empty()

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
    finally:
        st.session_state.downloading = False

st.button("Start Download", on_click=start_download)

if st.session_state.zip_data:
    st.download_button(
        label="⬇️ Download ZIP",
        data=st.session_state.zip_data,
        file_name="youtube_download.zip",
        mime="application/zip",
    )