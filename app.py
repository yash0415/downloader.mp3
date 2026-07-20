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
import shutil
import tempfile
import streamlit as st
import yt_dlp

st.set_page_config(page_title="Personal MP3 Downloader", page_icon="🎵")
st.title("🎵 Personal MP3 Downloader")

st.warning(
    "For personal use only. Only download content you have the rights to "
    "keep offline (your own uploads, Creative Commons tracks, or content "
    "you've licensed). Do not deploy this app publicly or share downloaded "
    "files with others."
)

st.info(
    "Files are processed in a temporary folder on the machine running this "
    "app and are deleted right after being sent to your browser — they are "
    "not kept permanently on this device."
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
        temp_dir = tempfile.mkdtemp(prefix="mp3_dl_")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
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
            "ignoreerrors": True,   # skip unavailable/broken entries instead of stopping
        }

        try:
            with st.spinner("Fetching info..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

            if info is None:
                st.error("This video/track is unavailable and could not be downloaded.")
                shutil.rmtree(temp_dir, ignore_errors=True)
                st.stop()

            def get_mp3_path(entry, ydl):
                """Ask yt-dlp for the exact filename it used, then swap ext to mp3."""
                raw_path = ydl.prepare_filename(entry)
                base, _ = os.path.splitext(raw_path)
                return base + ".mp3"

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if "entries" in info:
                    all_entries = info["entries"]
                    entries = [e for e in all_entries if e]
                    skipped = len(all_entries) - len(entries)
                    st.success(f"Ready: {len(entries)} track(s) — tap each to save to this device")
                    if skipped:
                        st.warning(f"⏭️ Skipped {skipped} unavailable track(s) and continued with the rest.")
                    for e in entries:
                        title = e.get("title", "unknown")
                        mp3_path = get_mp3_path(e, ydl)
                        if os.path.exists(mp3_path):
                            with open(mp3_path, "rb") as f:
                                st.download_button(
                                    label=f"⬇️ Save '{title}' to this device",
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
                    st.success(f"Ready: **{title}** — tap below to save to this device")
                    if os.path.exists(mp3_path):
                        with open(mp3_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Save to this device",
                                data=f.read(),
                                file_name=os.path.basename(mp3_path),
                                mime="audio/mpeg",
                            )
                    else:
                        st.write(f"⚠️ Couldn't locate file (looked for `{mp3_path}`)")

        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            # Clean up the temp copy now that bytes have been handed to the browser widgets above.
            # (Streamlit keeps the bytes in memory for the download_button, so it's safe to remove
            # the on-disk temp copy at this point.)
            shutil.rmtree(temp_dir, ignore_errors=True)

st.divider()
st.caption("No files are kept permanently on this machine — only in a temporary folder during processing.")