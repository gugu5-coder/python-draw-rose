#!/bin/bash
echo "测试玫瑰图生成服务..."
echo "===================================="

# 测试 1: 基本测试
echo -e "\n测试 1: 生成 10 瓣红色玫瑰，白色背景"
curl -X POST http://localhost:5000/draw_rose \
  -H "Content-Type: application/json" \
  -d '{"petals": 10, "color": "#FF0000", "bgcolor": "#FFFFFF"}' \
  -o test_rose_1.png
echo "已保存为 test_rose_1.png"

# 测试 2: 不同参数
echo -e "\n测试 2: 生成 7 瓣蓝色玫瑰，浅蓝背景"
curl -X POST http://localhost:5000/draw_rose \
  -H "Content-Type: application/json" \
  -d '{"petals": 7, "color": "#0000FF", "bgcolor": "#E0F7FA"}' \
  -o test_rose_2.png
echo "已保存为 test_rose_2.png"

# 测试 3: 参数验证 - 花瓣数超出范围
echo -e "\n测试 3: 验证花瓣数范围（应返回错误）"
curl -X POST http://localhost:5000/draw_rose \
  -H "Content-Type: application/json" \
  -d '{"petals": 25, "color": "#FF0000", "bgcolor": "#FFFFFF"}'

echo -e "\n===================================="
echo "测试完成！"
