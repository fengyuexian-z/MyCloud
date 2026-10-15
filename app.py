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

def scan_recursive(folder_path, base_folder_path, base_folder_name, recursive=True):
    """
    参数（当前文件夹地址，根文件夹地址，根文件夹名字，是否递归）

    大致思路：扫描folder_path，如果是支持的文件，加入images，如果是文件夹，递归调用返回sub_result，加入children（子树）
    拼url：先拿folder_path与base_folder_path求相对地址rel_path，转成url，然后f"/file(original)/base_folder_name/rel_url"

    递归扫描 folder_path，返回一个字典：
    {images:[{thumb_url: , ori_url: }], children:{
        "name": {
            "images": [],
            "children": {...} }
    """

    result = {"images":[],"children":{}}
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
                    "name" : item
                })
    return result

def flatten_tree(node, name, level, result, idx_list, all_origin):
    """
    node       : 当前子树，形如 {"images": [...], "children": {...}}
    name       : 当前文件夹显示名，比如 "2024" / "巴黎"
    level      : 层级，根 = 0
    result     : 最终扁平列表，元素为group{name, level, imades[]}，直接 append
    idx_list   : [0]，理解为 C++ 的 int&
    all_orgin  : 顺序收集原图 URL
    大致思路：先处理当前节点自身的images，分配全局index，然后加入group里，此时group已经完整，加入result，读image里的original_url加入all_origin
    然后在children递归调用，传子节点的children_node，children_name，level+1
    """
    group = {
        "name" : name,
        "level" : level,
        "images" : []
    }
    for img in node["images"]:
        img["index"] = idx_list[0]
        idx_list[0] +=1
        group["images"].append(img)
        all_origin.append(img["original_url"])

    result.append(group)

    for children_name, children_node in node["children"].items():
        flatten_tree(children_node, children_name, level+1, result, idx_list, all_origin)

    return result

@app.route('/')
def home():
    """
    这里负责给index.html提供数据，扫描根目录的下的第一层文件夹与图片，图片统一放入未分类相册，相册封面图默认为第一张(没有就为空)
    存入albums再交给前端渲染
    """
    try:
        source_entries=os.listdir(Source_Dir)
    except:
        return f"<h1>路径不存在：{Source_Dir}</h1>"

    albums=[]
    folders=[]
    root_images=[]
    for item in source_entries:
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