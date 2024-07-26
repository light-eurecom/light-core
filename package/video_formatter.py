from utils import logger
import ffmpeg

TARGET_SIZE_MB = 50


class VideoFormatter:
    def __init__(self, library):
        self.library = library
        
        
    def get_shortest_duration(self):
        """
        Returns the duration of the shortest video in the library.
        
        :return: Duration in seconds of the shortest video
        """
        min_duration = float('inf')
        for video in self.library:
            probe = ffmpeg.probe(video["path"])
            duration = float(probe['format']['duration'])
            if duration < min_duration:
                min_duration = duration
        return min_duration
    
    def format_videos(self):
        """
        Formats all videos to be the same duration by trimming them to the shortest video's duration
        and compressing them to fit the target size.
        
        :return: None
        """
        shortest_duration = self.get_shortest_duration()
        target_size_bytes = TARGET_SIZE_MB * 1024 * 1024  # Convert target size to bytes

        for video in self.library:
            logger.info(f"Processing {video['id']}...")

            # Calculate total bitrate for target size (video + audio)
            probe = ffmpeg.probe(video["path"])
            duration = float(probe['format']['duration'])
            total_bitrate = (target_size_bytes * 8) / duration  # in bits per second

            # Calculate video bitrate considering fixed audio bitrate
            audio_bitrate_kbps = int('128k'[:-1])  # Remove 'k' and convert to int
            video_bitrate = total_bitrate - (audio_bitrate_kbps * 1000)  # Total bitrate minus audio bitrate
            video_bitrate = video_bitrate / 1000  # Convert to kbits/s
            
            video_bitrate_str = f'{video_bitrate:.2f}k'
            minrate = video_bitrate_str
            maxrate = video_bitrate_str
            bufsize = f'{video_bitrate * 2:.2f}k'  # Buffer size is typically double the bitrate

            # Trim and compress video in a single step
            ffmpeg.input(video["path"], t=shortest_duration).output(
                video['compressed_path'],
                video_bitrate=video_bitrate_str,
                minrate=minrate,
                maxrate=maxrate,
                bufsize=bufsize,
                audio_bitrate='128k',  # Set a fixed audio bitrate
                vcodec='libx264',  # Use H.264 video codec
                acodec='aac',  # Use AAC audio codec
                format='mp4'
            ).run()

