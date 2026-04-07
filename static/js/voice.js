// This file contains JavaScript code for handling voice recognition. It interacts with the browser's Web Speech API to capture spoken answers and send them to the server for transcription.

const startButton = document.getElementById('start-recording');
const stopButton = document.getElementById('stop-recording');
const transcriptOutput = document.getElementById('transcript-output');

let recognition;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
} else {
    alert('Your browser does not support speech recognition. Please use Chrome or Firefox.');
}

recognition.continuous = false;
recognition.interimResults = false;
recognition.lang = 'en-US';

recognition.onstart = function() {
    console.log('Voice recognition started. Speak your answer.');
};

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    transcriptOutput.value = transcript;
    console.log('Transcript: ', transcript);
};

recognition.onerror = function(event) {
    console.error('Error occurred in recognition: ' + event.error);
};

startButton.addEventListener('click', function() {
    recognition.start();
});

stopButton.addEventListener('click', function() {
    recognition.stop();
});
