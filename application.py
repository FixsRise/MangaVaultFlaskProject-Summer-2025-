from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import boto3
from botocore.exceptions import ClientError
import pymysql
import re

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:admin123@manga-db.cs5df7cwdoht.us-east-1.rds.amazonaws.com:3306/manga_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Manga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True, nullable=False)
    upload_date = db.Column(db.DateTime, server_default=db.func.now())
    cover_url = db.Column(db.String(512), nullable=True)

S3_BUCKET = 'manga-upload-bucket'

def create_s3_client():
    return boto3.client('s3')

def safe_upload_file(fileobj, bucket, key):
    try:
        s3 = create_s3_client()
        s3.upload_fileobj(fileobj, bucket, key)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ExpiredToken':
            print("Token expired. Retrying upload...")
            s3 = create_s3_client()
            s3.upload_fileobj(fileobj, bucket, key)
        else:
            raise

@app.route('/')
def index():
    mangas = Manga.query.all()
    return render_template('index.html', mangas=mangas)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title'].strip()
        files = request.files.getlist('files')
        cover = request.files.get('cover')  

        existing = Manga.query.filter_by(title=title).first()
        if not existing:
            new_manga = Manga(title=title)
            db.session.add(new_manga)
            db.session.commit()
        else:
            new_manga = existing

        for index, file in enumerate(files):
            slide_number = index + 1
            filename = f"slide_{slide_number}.jpg"
            s3_key = f"manga/{title}/{filename}"
            safe_upload_file(file, S3_BUCKET, s3_key)

        if cover:
            cover_filename = "cover.jpg" 
            s3_key = f"manga/{title}/{cover_filename}"
            safe_upload_file(cover, S3_BUCKET, s3_key)
            cover_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"

            new_manga.cover_url = cover_url
            db.session.commit()

        return redirect(url_for('index'))

    return render_template('upload.html')
    
@app.route('/delete/<int:manga_id>', methods=['POST'])
def delete_manga(manga_id):
    manga = Manga.query.get_or_404(manga_id)

    s3 = create_s3_client()
    prefix = f"manga/{manga.title}/"
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
        if 'Contents' in response:
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': objects_to_delete})
    except ClientError as e:
        print(f"Error deleting S3 objects: {e}")


    db.session.delete(manga)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/manga/<title>')
def view_manga(title):
    try:
        s3 = create_s3_client()
        prefix = f"manga/{title}/"
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)

        def extract_slide_number(key):
            match = re.search(r'slide_(\d+)\.(jpg|jpeg|png|webp)$', key)
            return int(match.group(1)) if match else float('inf')

        files = []
        if 'Contents' in response:
            sorted_objs = sorted(
                response['Contents'],
                key=lambda obj: extract_slide_number(obj['Key'])
            )
            
            for obj in sorted_objs:
                key = obj['Key']
                if key.endswith('cover.jpg'):
                    continue  
                url = f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"
                files.append(url)
        else:
            files = []
    except ClientError as e:
        if e.response['Error']['Code'] == 'ExpiredToken':
            print("Token expired when listing objects.")
        else:
            print(f"S3 Fetch Error: {e}")
        files = []

    return render_template('manga_view.html', title=title, files=files)
    
    

if __name__ == "__main__": 
    app.run(host='0.0.0.0', port=8080, debug=True)
