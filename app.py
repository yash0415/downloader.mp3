"""
Personal MP3 Downloader — Streamlit + yt-dlp
=============================================
FOR PERSONAL, LOCAL USE ONLY.

This app is intended to run on your own machine for your own personal
listening (e.g. archiving content you own the rights to, or downloading
audio you have permission to keep offline). It is NOT intended to be
deployed publicly or shared as a service to others — doing so would
raise copyright/ToS concerns.

Run it with:
    streamlit run app.py
"""

import os
import streamlit as st
import yt_dlp

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "mp3_downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="Personal MP3 Downloader", page_icon="🎵")
st.title("🎵 Personal MP3 Downloader")

st.warning(
    "For personal use only. Only download content you have the rights to "
    "keep offline (your own uploads, Creative Commons tracks, or content "
    "you've licensed). Do not deploy this app publicly or share downloaded "
    "files with others."
)

url = st.text_input("YouTube URL (video or playlist)")
quality = st.selectbox("MP3 quality (kbps)", ["128", "192", "256", "320"], index=3)
is_playlist = st.checkbox("This is a playlist (download all tracks)")

progress_bar = st.progress(0)
status_text = st.empty()


def make_progress_hook():
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if total:
                progress_bar.progress(min(downloaded / total, 1.0))
            filename = os.path.basename(d.get("filename", ""))
            status_text.text(f"Downloading: {filename}")
        elif d["status"] == "finished":
            status_text.text("Converting to MP3...")
    return hook


if st.button("Download", type="primary"):
    if not url.strip():
        st.error("Please enter a URL.")
    else:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": quality,
                }
            ],
            "noplaylist": not is_playlist,
            "progress_hooks": [make_progress_hook()],
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with st.spinner("Fetching info..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

            def get_mp3_path(entry, ydl):
                """Ask yt-dlp for the exact filename it used, then swap ext to mp3."""
                raw_path = ydl.prepare_filename(entry)
                base, _ = os.path.splitext(raw_path)
                return base + ".mp3"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if "entries" in info:
                    entries = [e for e in info["entries"] if e]
                    st.success(f"Downloaded {len(entries)} tracks (saved on the server machine too)")
                    for e in entries:
                        title = e.get("title", "unknown")
                        mp3_path = get_mp3_path(e, ydl)
                        if os.path.exists(mp3_path):
                            with open(mp3_path, "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Download '{title}' to this device",
                                    data=f.read(),
                                    file_name=os.path.basename(mp3_path),
                                    mime="audio/mpeg",
                                    key=mp3_path,
                                )
                        else:
                            st.write(f"⚠️ Couldn't locate file for: {title} (looked for `{mp3_path}`)")
                else:
                    title = info.get("title", "unknown")
                    mp3_path = get_mp3_path(info, ydl)
                    st.success(f"Downloaded: **{title}** (saved on the server machine too)")
                    if os.path.exists(mp3_path):
                        with open(mp3_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download to this device",
                                data=f.read(),
                                file_name=os.path.basename(mp3_path),
                                mime="audio/mpeg",
                            )
                    else:
                        st.write(f"⚠️ Couldn't locate file (looked for `{mp3_path}`)")

        except Exception as e:
            st.error(f"Error: {e}")

st.divider()
st.caption(f"Files are saved locally to: `{DOWNLOAD_DIR}`")