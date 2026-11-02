import os, subprocess, json
from PIL import Image

#配置路径
Project_Path = os.path.dirname(os.path.abspath(__file__))
Source_Dir=os.path.expanduser("C:/Users/Lenovo_PC/Pictures")
Thumb_Dir = os.path.join(Project_Path,"thumbnails")

#缩略图大小及支持的格式
Thumb_Size = (600,600) 
Supported_Image=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
Supported_Video=['mp4', 'mov', 'avi', 'mkv', 'webm']

#创建文件夹
os.makedirs(Thumb_Dir, exist_ok=True)

success_img = 0
skipped_img = 0
failed_img  = 0
success_vid = 0
skipped_vid = 0
failed_vid  = 0

def thumb_image(item, full_path, thumb_path):
    global success_img, skipped_img, failed_img

    if os.path.exists(thumb_path):
        skipped_img += 1
        return True
    
    try:
        img=Image.open(full_path)
        img.thumbnail(Thumb_Size)
        # PNG 带透明通道的，转成 RGB 才能存 JPEG
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(thumb_path, quality=80)
        success_img += 1
        print(f"成功：{item}")

    except Exception as e:
        failed_img += 1
        print(f"{item} 失败：{e}")

def thumb_video(item, video_path, thumb_path):
    global success_vid, skipped_vid, failed_vid

    if os.path.exists(thumb_path):
        skipped_vid += 1

    else:
        if has_embedded_cover(video_path):
            if extract_cover(item, video_path, thumb_path):
                success_vid += 1
                print(f"成功（使用内嵌封面）：{item}")
                return True

        if run_ffmpeg_thumbnail(item, video_path, thumb_path):
            success_vid += 1
            print(f"成功（使用thumbnail 滤镜）：{item}")
            return True

        if run_ffmpeg_nonblack(video_path, thumb_path):
            success_vid += 1
            print(f"成功（使用第一个非黑帧）：{item}")
            return True

        failed_vid += 1
        return False

def has_embedded_cover(video_path):
    """判断视频有没有内嵌封面"""
    result = subprocess.run(
    ['ffprobe', '-v', 'quiet', '-print_format', 'json',
     '-show_streams', video_path],
    capture_output=True, text=True
    )
    if result.returncode != 0:
        return False

    info = json.loads(result.stdout)
    for stream in info.get('streams', []):
        if stream.get('disposition', {}).get('attached_pic') == 1:
            return True
    return False

def extract_cover(item, video_path, thumb_path):
    result = subprocess.run(
        ['ffmpeg', '-i', video_path,
        '-map', '0:v', '-map', '-0:V',   # 选所有视频流，排除主视频流
        '-frames:v', '1', '-q:v', '2',
        '-y', thumb_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"{item} 失败：{result.stderr}")
        return False

    return True

def run_ffmpeg_thumbnail(item, video_path, thumb_path):
    result = subprocess.run(
        ['ffmpeg', '-i', video_path,
        '-vf', 'thumbnail,scale=300:-1',
        '-frames:v', '1', '-q:v', '2',
        '-y', thumb_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
            print(f"{item} 失败：{result.stderr}")
            return False
    
    return True

def run_ffmpeg_nonblack(item, video_path, thumb_path):
    """提取第一个非黑帧（黑像素占比低于阈值的帧）"""
    result = subprocess.run(
        [
            'ffmpeg',
            '-ss', '0',
            '-i', video_path,
            '-vf', 'blackframe=0,metadata=select:key=lavfi.blackframe.pblack:value=50:function=less',
            '-frames:v', '1',
            '-q:v', '2',
            '-y',
            thumb_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"{item} 失败：{result.stderr}")
        return False

    return True

def thumbs(Folder_Dir,rel_path=""):
    """
    扫描Source_Dir的根文件夹下的item，如果是图片，调用thumbnail压缩；如果是视频，调用FFmpeg截取帧，如果视频有attached_pic就直接用(可能需要转换成jpg)，没有就thumbnail滤镜智能选帧，失败就用1s的帧兜底；
    如果是文件夹，递归调用扫描
    如何建目录：根据传入的rel_path参数，加上Thumb_Dir即为目录地址
    """
    global success_img, skipped_img, failed_img, success_vid, skipped_vid, failed_vid

    if os.path.isfile(Folder_Dir):
        return 0
    
    for item in os.listdir(Folder_Dir):
        full_path=os.path.join(Folder_Dir, item)

        if os.path.isdir(full_path):
            #递归调用
            sub_Folder_Dir=os.path.join(Folder_Dir, item)
            rel_Dir=os.path.relpath(sub_Folder_Dir, Source_Dir)
            thumbs(sub_Folder_Dir,rel_Dir)

        else:
            #判断格式
            ext=os.path.splitext(item)[1].lower().lstrip('.')
            if ext in Supported_Image:
                #得出缩略图在Thumb_Dir的位置,并建目录
                rel=os.path.join(Thumb_Dir,rel_path)
                os.makedirs(rel, exist_ok=True)
                thumb_path = os.path.join(rel,item)

                thumb_image(item, full_path, thumb_path)

            elif ext in Supported_Video:
                rel=os.path.join(Thumb_Dir,rel_path)
                os.makedirs(rel, exist_ok=True)
                thumb_path = os.path.join(rel,item) + ".jpg"
                thumb_video(item, full_path, thumb_path)

if __name__=='__main__':

    thumbs(Source_Dir,"")

    print(f"\n完成！")
    print(f"\n图片成功 {success_img} 张，跳过 {skipped_img} 张，失败 {failed_img} 张")
    print(f"\n视频成功 {success_vid} 条，跳过 {skipped_vid} 条，失败 {failed_vid} 条")