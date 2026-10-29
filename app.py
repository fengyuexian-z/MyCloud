from flask import Flask, send_from_directory, render_template
import os, json
from urllib.parse import quote

app=Flask(__name__)

Project_Path = os.path.dirname(os.path.abspath(__file__))
Thumb_Dir = os.path.join(Project_Path,"thumbnails")
Source_Dir=os.path.expanduser("C:/Users/Lenovo_PC/Pictures")
if not os.path.exists(Source_Dir):
    Source_Dir = "."

Supported_Image=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
Supported_Video=['mp4', 'mov', 'avi', 'mkv', 'webm']

def scan_recursive(folder_path, base_folder_path, base_folder_name, recursive=True):
    """
    参数（当前文件夹地址，根文件夹地址，根文件夹名字，是否递归）

    大致思路：扫描folder_path，如果是支持的文件，加入images/videos，如果是文件夹，递归调用返回sub_result，加入children（子树）
    拼url：先拿folder_path与base_folder_path求相对地址rel_path，转成url，然后f"/file(original)/base_folder_name/rel_url"

    递归扫描 folder_path，返回一个字典：
    {images:[{thumb_url: , original_url: }], videos:[{thumb_url: , original_url: }],children:{
        "name": {
            "images": [],
            "videos": [],
            "children": {...} }
    """

    result = {"images":[],
              "videos":[],
              "children":{}}
    for item in os.listdir(folder_path):
        full_path = os.path.join(folder_path,item)
        if os.path.isdir(full_path):
            if(recursive):
                sub_result = scan_recursive(full_path,base_folder_path,base_folder_name,recursive)
                result["children"][item] = sub_result   #注意是字典
        else:
            ext = os.path.splitext(item)[1].lower().lstrip('.')
            if ext in Supported_Image:
                rel_path = os.path.relpath(full_path,base_folder_path)
                rel_url = rel_path.replace("\\","/")
                thumb_url = f"/file/{base_folder_name}/{rel_url}"
                original_url = f"/original/{base_folder_name}/{rel_url}"
                result["images"].append({
                    "thumb_url" : thumb_url,
                    "original_url" : original_url,
                    "name" : item,
                })
            elif ext in Supported_Video:
                rel_path=os.path.relpath(full_path,base_folder_path)
                rel_url=rel_path.replace("\\","/")
                thumb_url= f"/file/{base_folder_name}/{rel_url}" + ".jpg"
                original_url=f"/original/{base_folder_name}/{rel_url}"
                result["videos"].append({
                    "thumb_url" : thumb_url,
                    "original_url" : original_url,
                    "name" : item
                })
                
    return result

def flatten_tree(node, name, level, result, idx_list, all_origin):
    """
    node       : 当前子树，形如 {"images": [...], "videos": [...], children": {...}}
    name       : 当前文件夹显示名，比如 "2024" / "巴黎"
    level      : 层级，根 = 0
    result     : 最终扁平列表，元素为group{name, level, images[], videos[]}，直接 append
    idx_list   : [0]，理解为 C++ 的 int&
    all_orgin  : 顺序收集原图 URL
    大致思路：先处理当前节点自身的images和videos，分配全局index，然后加入group里，此时group已经完整，加入result，读image里的original_url加入all_origin
    然后在children递归调用，传子节点的children_node，children_name，level+1
    """
    group = {
        "name" : name,
        "level" : level,
        "images" : [],
        "videos" : []
    }
    for img in node["images"]:
        img["index"] = idx_list[0]
        idx_list[0] +=1
        group["images"].append(img)
        all_origin.append(img["original_url"])
    for vde in node["videos"]:
        vde["index"] = idx_list[0]
        idx_list[0] +=1
        group["videos"].append(vde)
        all_origin.append(vde["original_url"])

    result.append(group)

    for children_name, children_node in node["children"].items():
        flatten_tree(children_node, children_name, level+1, result, idx_list, all_origin)

    return result

@app.route('/')
def home():
    """
    这里负责给index.html提供数据，扫描根目录的下的第一层文件夹和文件，文件统一放入未分类相册，相册封面图默认为第一张(没有就为空)
    存入albums再交给前端渲染
    数据结构：albums[{
        "name" : , #文件夹名
        "cover" : , #封面图
        "count" : , #内部文件个数
        "is_root" : , #判断是不是根目录下的文件
    }]
    """
    try:
        source_entries=os.listdir(Source_Dir)
    except:
        return f"<h1>路径不存在：{Source_Dir}</h1>"

    albums=[]
    folders=[]
    root_items=[]
    for item in source_entries:
        item_path=os.path.join(Source_Dir,item)
        if os.path.isdir(item_path):
            folders.append(item)
        else:
            ext = os.path.splitext(item)[1].lower().lstrip('.')
            if ext in Supported_Image or ext in Supported_Video:
                root_items.append(item)

    if root_items:
        cover_name = root_items[0] 
        if os.path.splitext(cover_name)[1].lower().lstrip('.') in Supported_Video:
            cover_name += ".jpg"
        root_cover = f"/file/{cover_name}"

        albums.append({
            "name" : "未分类",
            "cover": root_cover,
            "count": len(root_items),
            "is_root": True,
        })

    for folder in folders:
        folder_path=os.path.join(Source_Dir,folder)
        folder_items=[]
        try:
            files = os.listdir(folder_path)
        except:
            files = []

        for folder_item in files:
            ext = os.path.splitext(folder_item)[1].lower().lstrip('.')
            if ext in Supported_Image or ext in Supported_Video:
                folder_items.append(folder_item)
        
        cover = None
        if folder_items:
            cover_name = folder_items[0]
            if os.path.splitext(cover_name)[1].lower().lstrip('.') in Supported_Video:
                cover_name += ".jpg"
            cover = f"/file/{folder}/{quote(cover_name)}"
            
        albums.append({
            "name": folder,
            "cover": cover,
            "count": len(folder_items),
            "is_root": False,
        })
        
    return render_template("index.html",albums=albums, base_dir=Source_Dir)

@app.route('/album/<folder>')
def show_album(folder):
    """
    浏览器传入folder，将其作为根文件夹，scan_recursive遍历返回树，使用flatten_tree将路径扁平化后，将flat,folder,all_original返回给前端
    """
    folder_path=os.path.join(Source_Dir,folder)
    base_folder_path=os.path.join(Source_Dir,folder)
    base_folder_name=folder
    tree = scan_recursive(folder_path, base_folder_path, base_folder_name)

    idx_list = [0]
    all_original = []
    flat = flatten_tree(tree, folder, 0, [], idx_list, all_original)
    print(flat)
    return render_template("album.html", flat=flat, all_original=all_original, folder_name=folder)    
     
@app.route('/file/<path:filename>')
def send_files(filename):
    """
    这里给卡片网格缩略图，如果没有就给原图
    """
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