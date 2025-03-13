# 坐标排序工具

这个Python脚本用于处理包含glm::vec2坐标对的文件，将坐标按照从左上角到右下角的顺序进行排序。

## 功能

- 解析包含`glm::vec2`格式坐标的文件
- 按照从上到下、从左到右的顺序排序坐标
- 保持原始文件的大括号结构
- 输出排序后的结果到新文件或直接修改原文件
- 自动记录操作到log.md文件

## 排序规则

坐标排序优先级：
1. 按y坐标降序排序（从上到下）
2. 然后按x坐标升序排序（从左到右）

## 使用方法

```
python sort_coordinates.py [-h] [-i INPUT] [-o OUTPUT] [-m]
```

### 参数说明

- `-h, --help`: 显示帮助信息
- `-i INPUT, --input INPUT`: 输入文件路径（默认: "need repair.txt"）
- `-o OUTPUT, --output OUTPUT`: 输出文件路径（默认: 在输入文件名基础上添加"_sorted"后缀）
- `-m, --modify`: 直接修改原始文件，而不是创建新文件

### 示例

1. 使用默认设置（读取"need repair.txt"，输出到"need repair_sorted.txt"）:
```
python sort_coordinates.py
```

2. 指定输入文件:
```
python sort_coordinates.py -i my_coords.txt
```

3. 指定输入和输出文件:
```
python sort_coordinates.py -i input.txt -o output.txt
```

4. 直接修改原始文件:
```
python sort_coordinates.py -i my_coords.txt -m
```

## 注意事项

- 脚本会保持文件的原始括号结构
- 每次运行脚本后，操作会被记录到log.md文件中 