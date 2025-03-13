import os
from PIL import Image

def generate_ico(input_image_path, output_ico_path, sizes=None):
    """
    将图片转换为ICO文件
    
    Args:
        input_image_path (str): 输入图片路径
        output_ico_path (str): 输出ICO文件路径
        sizes (list): ICO尺寸列表，默认为[16, 32, 48, 64, 128, 256]
    """
    if sizes is None:
        sizes = [16, 32, 48, 64, 128, 256]
    
    try:
        # 打开原始图片
        img = Image.open(input_image_path)
        
        # 转换为RGBA模式（如果不是的话）
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建不同尺寸的图标
        icon_sizes = []
        for size in sizes:
            # 调整图片大小
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            icon_sizes.append(resized_img)
        
        # 保存为ICO文件
        icon_sizes[0].save(
            output_ico_path,
            format='ICO',
            sizes=[(size, size) for size in sizes],
            append_images=icon_sizes[1:]
        )
        
        print(f"成功生成ICO文件：{output_ico_path}")
        return True
        
    except Exception as e:
        print(f"生成ICO文件时发生错误：{str(e)}")
        return False

def main():
    # 示例使用
    print("Windows图标生成器")
    print("-" * 30)
    
    # 获取用户输入
    input_path = input("请输入源图片路径: ").strip()
    if not os.path.exists(input_path):
        print("错误：找不到输入文件！")
        return
    
    # 设置输出路径
    output_path = input("请输入输出ICO文件路径 (按回车使用默认路径): ").strip()
    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".ico"
    
    # 生成ICO
    success = generate_ico(input_path, output_path)
    
    if success:
        print("\n操作完成！")
    else:
        print("\n操作失败！")

if __name__ == "__main__":
    main() 