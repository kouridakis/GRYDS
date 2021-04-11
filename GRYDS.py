from pathlib import Path as p
from time import strftime
from platform import system
import PySimpleGUI as sg
import youtube_dl

def hook(d):
    # Convert the total size to megabytes
    total = float(d['total_bytes']) / 1024 / 1024

    # Extract the filename from the full path
    loc = d['filename'].rfind('\\') + 1
    name = d['filename'][loc:]

    # Limit the name to fit the output window
    sliced_name = name[:50]

    if d['status'] == 'downloading':
        window['URL_LIST'].update('Title: %s \nDownloading %.2f MB - %s' % (sliced_name, total, d['_percent_str']))
    
    if d['status'] == 'finished':
        window['URL_LIST'].update("%s \nDownload complete, converting... (Don't worry if the window freezes)" % (window['URL_LIST'].get()))
    
    # This allows for the percentage to update and the user to close the program
    event, values = window.read(timeout=100)
    if event == sg.WIN_CLOSED or event == 'Quit':
        quit()

errors = 0
class log(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        global errors
        # Write error messages into the log file
        dot = msg.find('.')
        error_msg = msg[:dot]
        log_file = open("gryds_log.txt", "a")
        log_file.write(error_msg + '\n')
        log_file.close()

        # Count the amount of errors
        errors += 1

# Initial values
audioformats = ["mp3", "aac", "flac", "m4a", "opus", "vorbis", "wav", "best"]
videoformats = ["mp4", "mkv", "ogg", "webm", "flv", "best"]
videoresolutions = ["480p", "720p", "1080p", "2160p"]
vidlist = []
videos = 0
dest = p("~/Downloads").expanduser()
ydl_opts = {
    'quiet': True,
    'ignoreerrors': True,
    'logger': log(),
    'progress_hooks': [hook]
}

icon = 'gryds.ico' if system() == 'Windows' else 'gryds.png'

sg.theme('DarkGreen3')
sg.set_global_icon(icon)

# Window layout
layout = [
    [sg.Text('Enter your URLs:', key='COUNTER')],
    [sg.Input(size=(52, 1), key='INPUT'), sg.Button('Add', bind_return_key=True)],
    [sg.Frame('Output', [
        [sg.Text('', size=(50, 3), key='URL_LIST')]
    ])],
    [sg.Frame('Options', [
    [sg.Radio('Video:', 'OUTPUTFORMAT', default = True, key='VIDEO'), sg.OptionMenu(videoformats, default_value='best', size=(5, 1), key='VIDEOFORMAT'), sg.OptionMenu(videoresolutions, default_value='1080p', size=(5, 1), key='VIDEORES'),
    sg.Text(''), sg.Radio('Audio only:', 'OUTPUTFORMAT', key='AUDIO'), sg.OptionMenu(audioformats, default_value='best', size=(5, 1), key='AUDIOFORMAT')],
    [sg.Text('Destination:'), sg.Input(str(dest), size=(33, 1), key='DESTFOLDER', disabled=True), sg.FolderBrowse(target='DESTFOLDER')]
    ])],
    [sg.Button('Download', size=(8, 1)), sg.Text('    '), sg.Button('Quit', size=(8, 1))]
]
window = sg.Window('GRYDS', layout, element_justification='center', element_padding=(2, 2), font=('Segoe', 10))

# Display a popup the first time the program is run
if p("gryds_log.txt").exists() == False:
    sg.popup("Most of this program's functionality relies on FFmpeg. Please make sure you have it installed.", title="IMPORTANT")
    log_file = open("gryds_log.txt", "x")
    log_file.close()

# Write the start time into the log file
log_file = open("gryds_log.txt", "a")
log_file.write("Start: " + strftime("%Y/%m/%d - %H:%M\n"))
log_file.close()

# Event loop
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Quit':
        break
    
    if event == 'Add':
        videos += 1
        vidlist.insert(0, values['INPUT'])
        window['URL_LIST'].update('%s\n%s' % (values['INPUT'], window['URL_LIST'].get()))
        window['COUNTER'].update('URLs added: %d' % (videos))
        window['INPUT'].update('')
    
    if event == 'Download':
        # Audio output
        if values['AUDIO'] == True:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['outtmpl'] = values['DESTFOLDER'] + r'/%(artist)s/%(title)s.%(ext)s'
            postprocessors = [{'key': 'FFmpegMetadata'}]
            if values['AUDIOFORMAT'] == 'best':
                postprocessors.append({'key': 'FFmpegExtractAudio'})
            else:
                postprocessors.append({'key': 'FFmpegExtractAudio', 'preferredcodec': values['AUDIOFORMAT']})
        # Video output
        else:
            vres = values['VIDEORES'].replace('p', '')
            ydl_opts['format'] = 'bestvideo[height<=%s]+bestaudio' % (vres)
            ydl_opts['outtmpl'] = values['DESTFOLDER'] + r'/%(title)s.%(ext)s'
            if values['VIDEOFORMAT'] == 'best':
                postprocessors = []
            else:
                postprocessors = [{'key': 'FFmpegVideoConvertor', 'preferedformat': values['VIDEOFORMAT']}]


        # Download the videos
        ydl_opts['postprocessors'] = postprocessors
        for url in vidlist:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        window['URL_LIST'].update('Process finished with %d errors, download list has been cleared. \nErrors can be found in the gryds_log.txt file (if any).' % (errors))
        window['COUNTER'].update('Enter your URLs:')
        vidlist = []
        videos = 0
        errors = 0
window.close()

# Write the end time into the log file
log_file = open("gryds_log.txt", "a")
log_file.write("Exit: " + strftime("%H:%M\n\n"))
log_file.close()
