from flask import Flask, send_from_directory
import os

app=Flask(__name__)

Project_Path = os.path.dirname(os.path.abspath(__file__))
Thumb_Dir = os.path.join(Project_Path,"thumbnails")
Source_Dir=os.path.expanduser("~/Pictures/Screenshots")
if not os.path.exists(Source_Dir):
    Source_Dir = "."

Supported_Image=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

@app.route('/')
def home():
    files=os.listdir(Source_Dir)
    html="<h1>我的云盘</h1><u1>"

    image=[]
    for f in files:
        ext=f.split('.')[-1].lower()
        if ext in Supported_Image:
            image.append(f)

    for img in image:
        html += f'<div style="margin:5px;"><img src="/file/{img}" loading="lazy" width="200" height="150" style="object-fit:cover;border-radius:8px;"/><br><span>{img}</span></div>'

    html += "</div>"
    return html

@app.route('/file/<path:filename>')
def send_files(filename):
    thumb_path = os.path.join(Thumb_Dir,filename)
    if(os.path.exists(thumb_path)):
        return send_from_directory(Thumb_Dir, filename)

    return send_from_directory(Source_Dir, filename)

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=True)