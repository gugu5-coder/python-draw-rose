#!/usr/bin/env python3
import os
import io
import base64
import tempfile
import subprocess
import time
from functools import wraps
from collections import OrderedDict
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)

class LRUCache:
    def __init__(self, capacity=10, ttl=60):
        self.capacity = capacity
        self.ttl = ttl
        self.cache = OrderedDict()
        self.timestamps = {}
    
    def get(self, key):
        if key not in self.cache:
            return None
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
        self.cache[key] = value
        self.timestamps[key] = time.time()

cache = LRUCache()

def generate_draw_script(petals, color, bgcolor):
    return f'''import turtle
import os
turtle.speed(0)
turtle.hideturtle()
turtle.colormode(255)

screen = turtle.Screen()
screen.bgcolor({tuple(int(bgcolor.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))})
turtle.pensize(2)
turtle.penup()
turtle.left(90)
turtle.fd(200)
turtle.pendown()
turtle.right(90)

turtle.fillcolor({tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))})
turtle.begin_fill()
turtle.circle(10,180)
turtle.circle(25,110)
turtle.left(50)
turtle.circle(60,45)
turtle.circle(20,170)
turtle.right(24)
turtle.fd(30)
turtle.left(10)
turtle.circle(30,110)
turtle.fd(20)
turtle.left(40)
turtle.circle(90,70)
turtle.circle(30,150)
turtle.right(30)
turtle.fd(15)
turtle.circle(80,90)
turtle.left(15)
turtle.fd(45)
turtle.right(165)
turtle.fd(20)
turtle.left(155)
turtle.circle(150,80)
turtle.left(50)
turtle.circle(150,90)
turtle.end_fill()

def draw_petal():
    turtle.left(150)
    turtle.circle(-90,70)
    turtle.left(20)
    turtle.circle(75,105)
    turtle.setheading(60)
    turtle.circle(80,98)
    turtle.circle(-90,40)
    turtle.left(180)
    turtle.circle(90,40)
    turtle.circle(-80,98)
    turtle.setheading(-83)

for _ in range({petals}):
    draw_petal()
    turtle.left(360/{petals})

turtle.penup()
turtle.goto(0, 0)
turtle.pendown()

canvas = screen.getcanvas()
canvas.postscript(file='/tmp/rose.eps')
turtle.bye()
'''

def draw_rose_image(petals, color, bgcolor):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(generate_draw_script(petals, color, bgcolor))
        script_path = f.name
    
    try:
        result = subprocess.run([
            'xvfb-run', '-a', 'python3', script_path
        ], capture_output=True, text=True, timeout=0.4)
        
        if os.path.exists('/tmp/rose.eps'):
            from PIL import Image
            img = Image.open('/tmp/rose.eps')
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            os.remove('/tmp/rose.eps')
            return img_buffer
        return None
    finally:
        os.unlink(script_path)

@app.route('/draw_rose', methods=['POST'])
def draw_rose():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    petals = data.get('petals', 10)
    color = data.get('color', '#FF0000')
    bgcolor = data.get('bgcolor', '#FFFFFF')
    
    try:
        petals = int(petals)
        if not (5 <= petals <= 20):
            return jsonify({'error': 'petals must be between 5 and 20'}), 400
    except ValueError:
        return jsonify({'error': 'petals must be an integer'}), 400
    
    cache_key = f"{petals}_{color}_{bgcolor}"
    cached_result = cache.get(cache_key)
    if cached_result:
        cached_img_buffer = io.BytesIO(cached_result)
        cached_img_buffer.seek(0)
        return send_file(cached_img_buffer, mimetype='image/png')
    
    img_buffer = draw_rose_image(petals, color, bgcolor)
    if img_buffer:
        cache.set(cache_key, img_buffer.getvalue())
        img_buffer.seek(0)
        return send_file(img_buffer, mimetype='image/png')
    
    return jsonify({'error': 'Failed to generate rose image'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
