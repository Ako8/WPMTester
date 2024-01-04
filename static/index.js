var socket = io();
var countdown = 60;
var timerInterval;
var gameIsOver = false;
var displayed = false
var username;

function sendSetupEvent(value) {
    socket.emit('setup', {'letters': value});
    location.reload();
}

socket.on('new_word', function (data) {
    displayWords(data.word, data.result)
    document.getElementById('typedWord').value = '';
    document.getElementById('result').textContent = '';
    gameIsOver = false;

    function updateTimer() {
        document.getElementById('time').textContent = countdown;
    }

    updateTimer();

    document.getElementById('typedWord').addEventListener('input', function () {
        if (gameIsOver) {
            this.value = '';
            return;
        }
        if (!timerInterval) {
            timerInterval = setInterval(function () {
                countdown--;
                updateTimer();

                if (countdown <= 0) {
                    clearInterval(timerInterval);
                    document.getElementById('result').textContent = 'Time is up! Game over.';
                    gameIsOver = true;
                }
            }, 1000);
        }
    });
});

function displayWords(words) {
    const wordList = document.getElementById('text');

    if (displayed) {
        wordList.innerHTML = '';
    }

    words.forEach(function (word) {
        const wordElement = document.createElement('span');
        wordElement.textContent = `${word.word} `;
        wordElement.id = `word-${word.id}`;


        if (word.result === "right") {
            wordElement.classList.add('right-word');
        } else if (word.result === "wrong") {
            wordElement.classList.add('wrong-word');
        }

        wordList.appendChild(wordElement);
    });
    displayed = true;


}

socket.on('game_over', function (data) {
    clearInterval(timerInterval);
    document.getElementById('result').textContent = 'WPM: ' + data.wpm;
    gameIsOver = true;
});

document.getElementById('resetButton').addEventListener('click', function () {
    countdown = 60
    socket.emit('reset_game');
});

socket.on('game_reset', function () {
    clearInterval(timerInterval);
    document.getElementById('text').textContent = '';
    document.getElementById('typedWord').value = '';
    document.getElementById('result').textContent = '';
    document.getElementById('time').textContent = '';
    gameIsOver = false;
});

document.getElementById('typedWord').addEventListener('keydown', function (event) {
    if (event.key === ' ' && !gameIsOver) {
        var typedWord = this.value;
        socket.emit('check_word', {'word': typedWord, 'took': 60 - countdown, 'name': username});
    }
});


var inputElement = document.getElementById('name');

var savedValue = localStorage.getItem('inputValue');
if (savedValue) {
    inputElement.value = savedValue;
}
username = savedValue
inputElement.addEventListener('input', function () {
    localStorage.setItem('inputValue', inputElement.value);
});