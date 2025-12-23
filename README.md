# MangaVaultFlaskProject-Summer-2025-

- Title: MangaVault – Cloud-Based Manga Library
- Author: Dmytro Kalinin

## Project description

MangaVault is a web application that allows users to upload, browse, and read manga (webcomics). Users can view manga titles, explore chapters, and leave comments on individual chapters. The app is designed to handle media uploads, manage metadata, and run efficiently on AWS infrastructure. It is built using Python and the Flask framework.

## Configuration architecture

AWS Database: Stores manga metadata, chapter info, and user comments (Amazon RDS – PostgreSQL)

S3: Stores manga cover images and chapter page files (JPG/PNG)

Pages: Home Page (list of manga), Manga Detail Page (chapters + comments), Upload Page (add manga and chapters)

Use Case: Online manga library for uploading, reading, and managing webcomics with reader comments

Framework & Runtime: Python Flask application deployed on AWS Elastic Beanstalk
