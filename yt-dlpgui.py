import sys
import yt_dlp
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, 
    QFileDialog, QTextEdit, QProgressBar, QCheckBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtCore import Qt
import logging
import shlex

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, url, quality, fileextension, custom_args, cookie_file, progress_bar=None, log_area=None, parent=None):
        super().__init__(parent)
        self.url = url
        self.quality = quality
        self.fileextension = fileextension
        self.custom_args = custom_args
        self.cookie_file = cookie_file
        self.progress_bar = progress_bar
        self.log_area = log_area

    def progress_hook(self, d): 
        if d['status'] == 'downloading':
            downloaded_bytes = d.get('downloaded_bytes', 0)
            total_bytes = d.get('total_bytes_estimate', d.get('total_bytes', 1))
            p = min(downloaded_bytes / max(total_bytes, 1), 1.0) * 100.0
            
            if self.progress_bar:
                self.progress_bar.setValue(int(p))
            
            if self.log_area:
                self.log_area.append(f'Downloading: {p:.1f}% ({downloaded_bytes}/{total_bytes} bytes)')

        elif d['status'] == 'finished':
            self.log_area.append('Finished downloading!')  
            self.progress_bar.setValue(100)

    def run(self):
        try:    
            quality_map = {
            'Best': 'bestvideo+bestaudio/best',
            '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            '720p': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
            '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
            '240p': 'bestvideo[height<=240]+bestaudio/best[height<=240]',
            '144p': 'bestvideo[height<=144]+bestaudio/best[height<=144]',
            'Audio Only': 'bestaudio/best'
        }
            ydl_opts = {
            'format': quality_map.get(self.quality, 'bestvideo+bestaudio/best'),   
            'progress_hooks': [self.progress_hook], 
            'outtmpl': '%(title)s.%(ext)s',
            'nooverwrites': False,  
            'no_color': True,      
            'ignoreerrors': True,  
            'fragment_retries': 10,
            'retries': 10,         
            'socket_timeout': 30,  
            'youtube_include_dash_manifest': False,
            'postprocessors': []
        }
                
            if self.cookie_file:
                ydl_opts['cookiefile'] = self.cookie_file

            if self.fileextension:
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': self.fileextension,
                })

                ydl_opts['postprocessor_args'] = {
                    'ffmpeg': [
                        '-preset', 'ultrafast',
                        '-threads', 'auto'
                    ]
                }

            if self.custom_args:
                import shlex
                custom_args_list = shlex.split(self.custom_args)
                for arg in custom_args_list:
                    if arg == '--write-thumbnail':
                        ydl_opts['writethumbnail'] = True
                    elif arg == '--embed-subs':
                        ydl_opts['writesubtitles'] = True 

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.finished_signal.emit('Your download is done!')

        except Exception as e:
            self.error_signal.emit(str(e))


                    


class YtDlpGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupStyles()
        self.cookie_file = None

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        def log_to_textarea(message, level=logging.INFO):
            self.log_area.append(message)
            if level == logging.ERROR:
                self.logger.error(message)
            else:
                self.logger.info(message)


    def initUI(self):
        self.setWindowTitle('Yt-Dlp GUI - By Jacob')
        self.setGeometry(100, 100, 600, 500)       
        central_widget = QWidget()
        main_layout = QVBoxLayout()
    
  
        url_layout = QVBoxLayout()
        url_label = QLabel('Enter URL: ')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('www.example.com/video')
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        custom_args_layout = QVBoxLayout()
        custom_args_label = QLabel('Custom yt-dlp Arguments:')
        self.custom_args_input = QLineEdit()
        self.custom_args_input.setPlaceholderText('--write-thumbnail --embed-subs')
        custom_args_layout.addWidget(custom_args_label)
        custom_args_layout.addWidget(self.custom_args_input)
        main_layout.addLayout(custom_args_layout)

        quality_layout = QVBoxLayout()
        quality_label = QLabel('Quality: ')
        self.quality_combo = QComboBox()  
        self.quality_combo.addItems(['Best', '1080p', '720p', '480p', '360p', '240p', '144p', 'Audio Only'])
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        main_layout.addLayout(quality_layout)

        fileextension_layout = QVBoxLayout()
        fileextension_label = QLabel('File extension')
        self.extension_combo = QComboBox()
        self.extension_combo.addItems(['mp4', 'wav', 'mp3', 'webm', 'mkv'])
        fileextension_layout.addWidget(fileextension_label)
        fileextension_layout.addWidget(self.extension_combo)
        main_layout.addLayout(fileextension_layout)

        button_layout = QHBoxLayout()  
        self.cookie_button = QPushButton('Upload Cookies')
        self.download_button = QPushButton('Download')
        button_layout.addWidget(self.cookie_button)
        button_layout.addWidget(self.download_button)
        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar) 

        self.log_area = QTextEdit()  
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.cookie_button.clicked.connect(self.upload_cookies)
        self.download_button.clicked.connect(self.download_video)


    def setupStyles(self):
        with open('style.qss', 'r') as f:
            stylesheet = f.read()
            self.setStyleSheet(stylesheet)

    def upload_cookies(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Upload your cookies")
        if file_name:
            self.cookie_file = file_name
            self.log_area.append(f"Cookies uploaded: {file_name}")
    
    def update_progress(self, progress, filename):
        self.progress_bar.setValue(progress)
        self.log_area.append(f'Downloading {filename}: {progress}%')
    
    def download_finished(self, message):
        self.log_area.append(message)
        self.progress_bar.setValue(100)
        self.log_area.append('Download completed succesfully!')

    def download_error(self, error_message):
        self.log_area.append(f'error: {error_message}')
    
    def download_video(self):
        url = self.url_input.text()
        quality = self.quality_combo.currentText()
        fileextension = self.extension_combo.currentText()
        custom_args = self.custom_args_input.text()

    
        if not url:
            self.log_area.append('Please enter a URL')
            return

        self.download_thread = DownloadThread(
            url, quality, fileextension, custom_args, self.cookie_file, progress_bar=self.progress_bar, log_area=self.log_area
        )
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.download_error)
        self.download_thread.start()
        
    
    def update_progress(self, progress, filename):
        self.progress_bar.setValue(progress)
        self.log_area.append(f'downloading {filename}: {progress}')


def main():
    app = QApplication(sys.argv)
    main_window = YtDlpGUI()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()