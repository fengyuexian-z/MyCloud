from flask import Flask, send_from_directory, render_template
import os
from urllib.parse import quote

app=Flask(__name__)

Project_Path = os.path.dirname(os.path.abspath(__file__))
Thumb_Dir = os.path.join(Project_Path,"thumbnails")
Source_Dir=os.path.expanduser("C:/Users/Lenovo_PC/Pictures")
if not os.path.exists(Source_Dir):
    Source_Dir = "."

Supported_Image=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

def scan_recursive(folder_path, base_folder, folder_name, recursive=True):
    """
    递归扫描 folder_path，返回一个字典：
    {子文件夹相对路径: [{缩略图url: , 原图url: }]}
    """
    result = {}
    for item in os.listdir(folder_path):
        full_path=os.path.join(folder_path,item)
        if os.path.isdir(full_path):
            if recursive:
                sub_result=scan_recursive(full_path,base_folder,folder_name, recursive)
                for sub_folder, images in sub_result.items():
                    if sub_folder in result:
                        result[sub_folder].extend(images)
                    else:
                        result[sub_folder]=images
  
        else:
            ext=os.path.splitext(item)[1].lower().lstrip('.')
            if ext in Supported_Image:
                rel_path=os.path.relpath(full_path, base_folder)
                sub_path=os.path.dirname(rel_path)
                if sub_path=="":
                    sub_path="未分类"

                rel_url=rel_path.replace("\\","/")
                thumb_url    = f"/file/{folder_name}/{rel_url}"
                original_url = f"/original/{folder_name}/{rel_url}"

                if sub_path not in result:
                    result[sub_path] = []
                result[sub_path].append({
                    "thumb":    thumb_url,
                    "original": original_url,
                })
                
    return result
    

@app.route('/')
def home():
    try:
        items=os.listdir(Source_Dir)
    except:
        return f"<h1>路径不存在：{Source_Dir}</h1>"

    albums=[]
    folders=[]
    root_images=[]
    for item in items:
        item_path=os.path.join(Source_Dir,item)
        if os.path.isdir(item_path):
            folders.append(item)
        else:
            if os.path.splitext(item)[1].lower().lstrip('.') in Supported_Image:
                root_images.append(item)

    if root_images:
        albums.append({
            "name" : "未分类",
            "cover": f"/file/{quote(root_images[0])}",
            "count": len(root_images),
            "is_root": True,
        })

    for folder in folders:
        folder_path=os.path.join(Source_Dir,folder)
        try:
            files = os.listdir(folder_path)
        except:
            files = []

        images=[i for i in files if os.path.splitext(i)[1].lower().lstrip('.') in Supported_Image]
        cover_img=images[0] if images else None

        albums.append({
            "name": folder,
            "cover":f"/file/{folder}/{quote(cover_img)}" if cover_img else None,
            "count": len(images),
            "is_root": False,
        })
        
    return render_template("index.html",albums=albums, base_dir=Source_Dir)

@app.route('/album/<folder>')
def show_album(folder):
    if folder == "未分类":
        folder_path=Source_Dir
        base_path=Source_Dir
        folder_name=""
        if not os.path.exists(folder_path):
                return "<h1>相册不存在</h1><a href='/'>返回</a>"
        
        group = scan_recursive(folder_path, base_path, folder_name, False)
    else:
        folder_path = os.path.join(Source_Dir, folder)
        base_folder = folder_path
        folder_name = folder
        if not os.path.exists(folder_path):
                return "<h1>相册不存在</h1><a href='/'>返回</a>"
        
        group = scan_recursive(folder_path, base_folder, folder_name)

    all_orgin=[]
    idx=0
    for sub_folder, images in group.items():
        for img in images:
            img["index"]=idx
            all_orgin.append(img["original"])
            idx+=1

    return render_template("album.html",all_orgin=all_orgin,group=group,folder_name=folder)
     
@app.route('/file/<path:filename>')
def send_files(filename):
    if filename.split("/",1)[0]=="未分类":
        filename=os.path.basename(filename)
    thumb_path = os.path.join(Thumb_Dir,filename)
    if(os.path.exists(thumb_path)):
        return send_from_directory(Thumb_Dir, filename)

    return send_from_directory(Source_Dir, filename)

@app.route('/original/<path:filename>')
def send_original(filename):
    if filename.split("/",1)[0]=="未分类":
            filename=os.path.basename(filename)
    return send_from_directory(Source_Dir, filename)

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5000,debug=True,threaded=True)