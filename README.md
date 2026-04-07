# AI Virtual Exam Scribe

An AI-powered web application designed for users who are unable to write exams using their hands due to physical disabilities or temporary injuries. The system enables users to listen to questions, respond through speech, and navigate the exam entirely using voice interaction.

---

## Overview

AI Virtual Exam Scribe provides a hands-free examination experience for individuals who do not have functional use of their hands. By integrating speech recognition and audio feedback, the system allows users to independently attempt exams without relying on manual input.

The platform also includes an admin interface for managing students, monitoring submissions, and maintaining exam data.

---

## Problem Statement

Traditional online examination systems require manual input through keyboards or writing, making them inaccessible for individuals who cannot use their hands due to disability or injury. This creates a significant barrier to equal participation in academic and professional assessments.

---

## Solution

This project introduces a voice-based examination system that allows users to:

* Navigate questions using voice commands
* Listen to questions through audio playback
* Answer questions using speech-to-text
* Complete exams without any physical interaction

---

## Features

### Student Side

* Voice-based question navigation
* Speech-to-text answer input
* Audio playback of questions
* Completely hands-free exam interaction
* Automatic submission on timeout

### Admin Side

* Admin login system
* Add and manage student records
* View exam submissions
* Monitor student performance
* Database management

### System Features

* Face image storage for verification
* JSON-based question management
* Audio alerts for actions (start, submit, warning)
* Clean and responsive user interface

---

## Tech Stack

* Frontend: HTML, CSS, JavaScript
* Backend: Python (Flask)
* Database: SQLite
* Speech Processing: Web Speech API / Python-based handling
* Version Control: Git and GitHub

---

## Project Structure

AI-Virtual-Exam-Scribe/
│
├── static/            # CSS, JS, audio files
├── templates/         # HTML templates
├── faces/             # Student face images
├── transcripts/       # Stored transcripts
├── instance/          # Database (ignored in Git)
├── requirements.txt   # Dependencies
├── questions.json     # Exam questions
├── upgrade2.py        # Main application logic
├── upgrade3.py        # Extended functionality
└── README.md

---

## Installation and Setup

### 1. Clone the repository

git clone https://github.com/Prithivirajan-J/Ai-Scribe.git
cd Ai-Scribe

### 2. Create virtual environment

python -m venv venv
venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Run the application

python upgrade2.py

---

## Usage

* Open the application in your browser
* Select role (Admin or Student)
* Admin can manage students and exam data
* Students can take exams using voice interaction without using hands

---

## Future Improvements

* Real-time face verification integration
* Improved speech recognition accuracy using advanced AI models
* Cloud-based database integration
* Mobile-friendly interface
* Multi-language voice support

---

## Author

Prithivi Rajan

---

## Notes

This project focuses on accessibility and aims to ensure that individuals with physical limitations affecting hand usage can participate in digital examinations independently and efficiently.
