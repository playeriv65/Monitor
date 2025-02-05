import os
import json
import shutil

def init_json_file():
    """初始化fall_record.json为空数组"""
    with open("fall_record.json", "w") as f:
        json.dump([], f, indent=4)

def clear_picture_folder():
    """清空picture文件夹"""
    picture_dir = "picture"
    # 确保picture文件夹存在
    if not os.path.exists(picture_dir):
        os.makedirs(picture_dir)
    # 删除文件夹内所有文件
    for file in os.listdir(picture_dir):
        file_path = os.path.join(picture_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    # 执行初始化操作
    init_json_file()
    clear_picture_folder()
    print("初始化完成!")