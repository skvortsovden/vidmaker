import os
import ffmpeg
import tkinter as tk
from tkinter import filedialog, messagebox
import datetime

def merge_videos(video_files, output_file):
    """Merges video files into one with optimization"""
    # Create an in-memory list of input files for ffmpeg
    inputs = [ffmpeg.input(video) for video in video_files]
    
    # Concatenate the videos
    ffmpeg.concat(*inputs, v=1, a=1).output(
        output_file, vcodec='libx264', crf=23, preset='fast', acodec='aac'
    ).run()

def add_watermark(input_video, watermark_image, output_video):
    """Adds a watermark across the entire width of the video with 50% transparency and optimization"""
    video = ffmpeg.input(input_video)
    watermark = ffmpeg.input(watermark_image, loop=1).filter("format", "rgba").filter("colorchannelmixer", aa=0.3)

    # Get the duration of the video
    probe = ffmpeg.probe(input_video, v='error', select_streams='v:0', show_entries='stream=duration,width,height')
    duration = float(probe['streams'][0]['duration'])

    # Get the size of the video
    width = int(probe['streams'][0]['width']) if 'width' in probe['streams'][0] else 1280
    height = int(probe['streams'][0]['height']) if 'height' in probe['streams'][0] else 720
    
    # Stretch the watermark across the width of the video
    watermark = watermark.filter("scale", width, -1)
    
    # Set the duration of the watermark
    watermark = watermark.filter("trim", duration=duration)
    
    output = ffmpeg.overlay(video, watermark, x=0, y="(H-h)/2")
    ffmpeg.output(
        output, output_video, vcodec='h264_videotoolbox', crf=23, preset='fast', acodec='aac'
    ).run()

def add_audio(input_video, audio_file, output_video):
    """Adds music to the video with optimization"""

    # Get the duration of the video
    probe = ffmpeg.probe(input_video, v='error', select_streams='v:0', show_entries='stream=duration,width,height')
    duration = float(probe['streams'][0]['duration'])

    trimmed_audio = trim_audio(audio_file, duration)

    video = ffmpeg.input(input_video)
    audio = ffmpeg.input(trimmed_audio)
    ffmpeg.output(
        video, audio, output_video, vcodec='h264_videotoolbox', crf=23, preset='fast', acodec='aac'
    ).run()

def trim_audio(input_file, duration):
    """
    Trims an audio file from the beginning for the given duration and saves it 
    next to the original file with a '_trimmed' suffix.

    :param input_file: Path to the input audio file.
    :param duration: Duration in seconds.
    :return: Path to the trimmed audio file.
    """
    # Generate the output file path with '_trimmed' suffix
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_trimmed{ext}"

    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, t=duration, codec="copy")
            .run(overwrite_output=True, quiet=True)
        )
        print(f"Trimmed audio saved as: {output_file}")
        return output_file
    except ffmpeg.Error as e:
        print(f"Error trimming audio: {e}")
        return None

def select_files(filetypes, multiple=True):
    """File selection function via UI"""
    filenames = filedialog.askopenfilenames(filetypes=filetypes) if multiple else filedialog.askopenfilename(filetypes=filetypes)
    return list(filenames) if multiple else filenames

def clean_up_files(*files):
    """
    Deletes the specified files if they exist.
    
    :param files: List of file paths to check and delete.
    """
    for file in files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Deleted existing file: {file}")
        else:
            print(f"File not found, skipping: {file}")

def process_files(video_files, watermark_image, audio_file):
    merged_video = "merged.mp4"
    watermarked_video = "watermarked.mp4"
    
    # Generate a unique name for the final output file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    final_video = f"vidmaker_{timestamp}.mp4"

    # Clean up existing files before processing
    clean_up_files(merged_video, watermarked_video, final_video)

    try:
        merge_videos(video_files, merged_video)
        add_watermark(merged_video, watermark_image, watermarked_video)
        add_audio(watermarked_video, audio_file, final_video)

        messagebox.showinfo("Done", f"The final video has been saved as {final_video}")
    finally:
        # Clean up intermediate files after processing
        clean_up_files(merged_video, watermarked_video)

def open_ui():
    root = tk.Tk()
    root.title("Video Editing Automation")
    root.geometry("600x400")  # Increased size for better visibility

    video_files = []
    watermark_image = ""
    audio_file = ""

    def select_videos():
        nonlocal video_files
        video_files = select_files([("Video files", "*.mp4 *.avi *.mov")])
        if video_files:
            video_text.delete("1.0", tk.END)  # Clear existing text
            video_text.insert(tk.END, "\n".join(video_files))  # Insert selected files
        else:
            video_text.delete("1.0", tk.END)
            video_text.insert(tk.END, "No files selected")
    
    def select_watermark():
        nonlocal watermark_image
        watermark_image = select_files([("Image files", "*.png *.jpg *.jpeg")], multiple=False)
        if watermark_image:
            watermark_text.delete("1.0", tk.END)
            watermark_text.insert(tk.END, watermark_image)
        else:
            watermark_text.delete("1.0", tk.END)
            watermark_text.insert(tk.END, "No file selected")
    
    def select_audio():
        nonlocal audio_file
        audio_file = select_files([("Audio files", "*.mp3 *.wav")], multiple=False)
        if audio_file:
            audio_text.delete("1.0", tk.END)
            audio_text.insert(tk.END, audio_file)
        else:
            audio_text.delete("1.0", tk.END)
            audio_text.insert(tk.END, "No file selected")
    
    def start_processing():
        if not video_files or not watermark_image or not audio_file:
            messagebox.showwarning("Error", "Please select all files before starting the process")
            return
        process_files(video_files, watermark_image, audio_file)
    
    # UI Elements
    tk.Button(root, text="Select Video Files", command=select_videos).pack(pady=5)
    video_text = tk.Text(root, height=4, wrap="word", bg="white", fg="red", relief="solid")
    video_text.insert(tk.END, "No files selected")
    video_text.pack(fill="x", padx=10, pady=5)

    tk.Button(root, text="Select Watermark", command=select_watermark).pack(pady=5)
    watermark_text = tk.Text(root, height=2, wrap="word", bg="white", fg="red", relief="solid")
    watermark_text.insert(tk.END, "No file selected")
    watermark_text.pack(fill="x", padx=10, pady=5)

    tk.Button(root, text="Select Audio File", command=select_audio).pack(pady=5)
    audio_text = tk.Text(root, height=2, wrap="word", bg="white", fg="red", relief="solid")
    audio_text.insert(tk.END, "No file selected")
    audio_text.pack(fill="x", padx=10, pady=5)

    tk.Button(root, text="Start Processing", command=start_processing).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    open_ui()
