import os
import platform
from flask import Flask, send_file, jsonify, request, render_template_string

app = Flask(__name__)

bootstrap_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Browser</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h1 class="my-4">{{ title }}</h1>
        <ul class="list-group">
            {% for item in items %}
            <li class="list-group-item">
                <a href="{{ item.url }}">{{ item.name }}</a>
            </li>
            {% endfor %}
        </ul>
    </div>
</body>
</html>
'''

def get_root_directory():
    system = platform.system()
    if system == "Windows":
        return "C:\\"
    elif system == "Linux":
        # On Android, the OS is recognized as Linux
        if os.path.exists("/storage/emulated/0"):
            return "/storage/emulated/0"
        else:
            return "/"
    elif system == "Darwin":
        return "/"
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")

root_dir = get_root_directory()

@app.route('/')
def home():
    file_types = ['txt', 'pdf', 'jpg', 'png', 'mp4', 'mkv']  # Add more types as needed
    items = [{'name': f'{file_type.upper()} Files', 'url': f'/files/{file_type}'} for file_type in file_types]
    items.append({'name': 'Browse by yourself', 'url': '/browse/'})
    return render_template_string(bootstrap_template, title='Select File Type', items=items)

@app.route('/files/<file_type>')
def list_files_by_type(file_type):
    files = []
    for root, dirs, file_list in os.walk(root_dir):
        for file in file_list:
            if file.endswith(f".{file_type}"):
                files.append(os.path.join(root, file))
                
    if not files:
        return jsonify({"error": f"No {file_type} files found in the root directory"})
    
    items = [{'name': file.replace(root_dir, '~'), 'url': f'/download?file={file}'} for file in files]
    return render_template_string(bootstrap_template, title=f'List of {file_type.upper()} Files', items=items)

@app.route('/browse/', defaults={'path': ''})
@app.route('/browse/<path:path>')
def browse_files(path):
    full_path = os.path.join(root_dir, path)
    
    if not os.path.exists(full_path):
        return jsonify({"error": "Directory not found"})
    
    if os.path.isfile(full_path):
        return send_file(full_path, as_attachment=True)
    
    items = []
    if path:
        parent_path = os.path.join(path, '..')
        items.append({'name': '.. (Parent Directory)', 'url': f'/browse/{parent_path}'})
    
    for item in os.listdir(full_path):
        item_path = os.path.join(path, item)
        if os.path.isdir(os.path.join(root_dir, item_path)):
            items.append({'name': f'{item}/', 'url': f'/browse/{item_path}'})
        else:
            items.append({'name': item, 'url': f'/download?file={os.path.join(root_dir, item_path)}'})
    
    return render_template_string(bootstrap_template, title=f'Browsing: {full_path.replace(root_dir, "~")}', items=items)

@app.route('/download')
def download_file():
    file_path = request.args.get('file')
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"error": "File not found"})
    
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
