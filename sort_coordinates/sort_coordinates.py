import re
import datetime
import argparse

def parse_coordinates(file_path):
    """解析文件中的坐标数据"""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # 提取所有坐标对
    pattern = r'glm::vec2\((-?\d+\.\d+), (-?\d+\.\d+)\),glm::vec2\((-?\d+\.\d+), (-?\d+\.\d+)\)'
    matches = re.findall(pattern, content)
    
    # 提取外层结构，保留大括号信息
    structure_pattern = r'(\{+)(.*)(\}+)'
    structure_match = re.search(structure_pattern, content)
    opening_braces = structure_match.group(1)
    closing_braces = structure_match.group(3)
    
    # 解析为两个主要组
    main_groups = content.split('},{{')
    if len(main_groups) > 1:
        first_group = main_groups[0].strip('{')
        second_group = main_groups[1].strip('}')
        
        # 提取第一组和第二组的坐标
        first_group_pattern = r'glm::vec2\((-?\d+\.\d+), (-?\d+\.\d+)\),glm::vec2\((-?\d+\.\d+), (-?\d+\.\d+)\)'
        first_group_matches = re.findall(first_group_pattern, first_group)
        second_group_matches = re.findall(first_group_pattern, second_group)
        
        return opening_braces, closing_braces, first_group_matches, second_group_matches
    
    # 如果无法分割为两组，则返回所有匹配项作为一组
    return opening_braces, closing_braces, matches, []

def sort_coordinates(coords):
    """
    按从左上角到右下角的顺序排序坐标
    优先级：y坐标降序（从上到下），然后x坐标升序（从左到右）
    """
    # 将字符串转换为浮点数
    coords_float = []
    for coord in coords:
        x1, y1, x2, y2 = map(float, coord)
        coords_float.append((x1, y1, x2, y2))
    
    # 先根据左上角y坐标降序排序（从上到下），然后按左上角x坐标升序排序（从左到右）
    sorted_coords = sorted(coords_float, key=lambda c: (-c[1], c[0]))
    
    return sorted_coords

def format_coordinates(sorted_coords):
    """将排序后的坐标格式化为原始格式"""
    formatted = []
    for x1, y1, x2, y2 in sorted_coords:
        formatted.append(f'glm::vec2({x1}, {y1}),glm::vec2({x2}, {y2})')
    return formatted

def write_sorted_coordinates(file_path, opening_braces, closing_braces, first_group, second_group):
    """将排序后的坐标写入文件"""
    with open(file_path, 'w') as file:
        file.write(opening_braces)
        
        # 写入第一组坐标
        for i, coord in enumerate(first_group):
            if i > 0:
                file.write(',')
            file.write('{' + coord + '}')
        
        # 如果有第二组，添加分隔符并写入
        if second_group:
            file.write('},{')
            for i, coord in enumerate(second_group):
                if i > 0:
                    file.write(',')
                file.write('{' + coord + '}')
        
        file.write(closing_braces)

def update_log(action):
    """更新log.md文件"""
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    log_entry = f"# {date}\n## {time}\n    {action}\n"
    
    with open("log.md", 'a') as log_file:
        log_file.write(log_entry)

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='按从左上角到右下角的顺序排序坐标')
    parser.add_argument('-i', '--input', default="need repair.txt", help='输入文件路径 (默认: need repair.txt)')
    parser.add_argument('-o', '--output', help='输出文件路径 (默认: 与输入文件相同或添加"_sorted"后缀)')
    parser.add_argument('-m', '--modify', action='store_true', help='直接修改原始文件')
    args = parser.parse_args()
    
    input_file = args.input
    
    # 确定输出文件
    if args.modify:
        output_file = input_file
    elif args.output:
        output_file = args.output
    else:
        # 在文件名和扩展名之间添加"_sorted"
        name_parts = input_file.rsplit('.', 1)
        if len(name_parts) > 1:
            output_file = f"{name_parts[0]}_sorted.{name_parts[1]}"
        else:
            output_file = f"{input_file}_sorted"
    
    # 解析坐标
    opening_braces, closing_braces, first_group_matches, second_group_matches = parse_coordinates(input_file)
    
    # 排序第一组坐标
    sorted_first_group = sort_coordinates(first_group_matches)
    formatted_first_group = format_coordinates(sorted_first_group)
    
    # 排序第二组坐标 (如果有)
    sorted_second_group = []
    formatted_second_group = []
    if second_group_matches:
        sorted_second_group = sort_coordinates(second_group_matches)
        formatted_second_group = format_coordinates(sorted_second_group)
    
    # 写入排序后的坐标
    write_sorted_coordinates(output_file, opening_braces, closing_braces, 
                           formatted_first_group, formatted_second_group)
    
    # 更新日志
    if args.modify:
        update_log(f"使用sort_coordinates.py将{input_file}中的坐标按从左上角到右下角的顺序排序并直接修改原文件")
    else:
        update_log(f"使用sort_coordinates.py将坐标按从左上角到右下角的顺序排序，从{input_file}生成{output_file}")
    
    print(f"坐标已排序并保存到 {output_file}")

if __name__ == "__main__":
    main() 