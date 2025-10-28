
import os
import shutil

def clean_directories(dirs):
    """
    删除指定目录列表下的所有内容（文件和子目录）
    :param dirs: 目录路径列表
    """
    for dir_path in dirs:
        if os.path.exists(dir_path):
            for filename in os.listdir(dir_path):
                file_path = os.path.join(dir_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'删除 {file_path} 时出错: {e}')
        else:
            print(f'目录不存在: {dir_path}')
    print("清理完成。")

# 用法示例


