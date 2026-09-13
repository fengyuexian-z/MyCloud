import os
from PIL import Image

#配置路径
Project_Path = os.path.dirname(os.path.abspath(__file__))
Source_Dir=os.path.expanduser("C:/Users/Lenovo_PC/Pictures")
Thumb_Dir = os.path.join(Project_Path,"thumbnails")

#缩略图大小及支持的格式
Thumb_Size = (300,300) 
Supported_Image=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']

#创建文件夹
os.makedirs(Thumb_Dir, exist_ok=True)

success = 0
skipped = 0
failed  = 0

def thumbs(File_Dir,rel_path=""):
    global success, skipped, failed

    if os.path.isfile(File_Dir):
        return 0
    
    for filename in os.listdir(File_Dir):
        full_path=os.path.join(File_Dir,filename)
        if os.path.isfile(full_path):
            #判断格式
            ext=os.path.splitext(filename)[1].lower().lstrip('.')
            if ext not in Supported_Image:
                continue

            #得出缩略图在Thumb_Dir的位置,并建目录
            rel=os.path.join(Thumb_Dir,rel_path)
            os.makedirs(rel, exist_ok=True)
            thumb_path = os.path.join(rel,filename)
            

            if os.path.exists(thumb_path):
                skipped += 1
                continue

            try:
                img=Image.open(full_path)
                img.thumbnail(Thumb_Size)
                # PNG 带透明通道的，转成 RGB 才能存 JPEG
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(thumb_path, quality=80)
                success += 1
                print(f"成功：{filename}")

            except Exception as e:
                failed += 1
                print(f"{filename} 失败：{e}")
        else:
            #递归调用
            Folder_Dir=os.path.join(File_Dir,filename)
            rel_Dir=os.path.relpath(Folder_Dir,Source_Dir)
            thumbs(Folder_Dir,rel_Dir)

    return 0

if __name__=='__main__':

    thumbs(Source_Dir,"")

    print(f"\n完成！成功 {success} 张，跳过 {skipped} 张，失败 {failed} 张")