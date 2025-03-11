document.addEventListener("DOMContentLoaded", function() {
    // Playlist array
    const playlist = {
        home: '/static/music2.mp3',  // Played on welcome, index, and lobby
        game: '/static/music.mp3'    // Played during game and final scoreboard
    };
    let currentTrack = playlist.home; // Default to home music
    let audioElement = new Audio(currentTrack);
    audioElement.loop = true; // Loop music for continuous play
    audioElement.volume = 0.3;

    // Sound effects
    const selectSound = new Audio('/static/select.mp3');
    const submitSound = new Audio('/static/submit.mp3');
    const correctSound = new Audio('/static/correct.mp3');
    const roundEndSound = new Audio('/static/round_end.mp3');
    selectSound.volume = 0.5;
    submitSound.volume = 0.5;
    correctSound.volume = 0.5;
    roundEndSound.volume = 0.5;

    // DOM elements
    const musicControlBtn = document.getElementById("music-control-btn");
    const muteBtn = document.getElementById("mute-btn");

    // Load saved state from sessionStorage
    const savedState = {
        isPlaying: sessionStorage.getItem("musicIsPlaying") === "true",
        currentTime: parseFloat(sessionStorage.getItem("musicCurrentTime")) || 0,
        isMuted: sessionStorage.getItem("musicIsMuted") === "true"
    };

    // Apply saved state
    audioElement.currentTime = savedState.currentTime;
    audioElement.muted = savedState.isMuted || false; // Not muted by default for autoplay

    // Autoplay on page load
    audioElement.play().catch(() => console.log("Autoplay blocked until user interaction"));

    // Toggle music player visibility (for non-game pages)
    if (musicControlBtn) {
        musicControlBtn.addEventListener("click", function() {
            const musicPlayer = document.getElementById("music-player");
            if (musicPlayer) musicPlayer.classList.toggle("active");
        });
    }

    // Mute/Unmute toggle
    if (muteBtn) {
        muteBtn.addEventListener("click", function() {
            audioElement.muted = !audioElement.muted;
            sessionStorage.setItem("musicIsMuted", audioElement.muted);
            muteBtn.classList.toggle("btn-muted", audioElement.muted);
        });
    }

    // Save current time periodically
    audioElement.addEventListener("timeupdate", function() {
        sessionStorage.setItem("musicCurrentTime", audioElement.currentTime);
    });

    // Handle page unload to save final state
    window.addEventListener("beforeunload", function() {
        sessionStorage.setItem("musicIsPlaying", !audioElement.paused);
        sessionStorage.setItem("musicCurrentTime", audioElement.currentTime);
        sessionStorage.setItem("musicIsMuted", audioElement.muted);
    });

    // Expose functions for game-specific music control and sound effects
    window.switchToGameMusic = function() {
        if (currentTrack !== playlist.game) {
            currentTrack = playlist.game;
            audioElement.src = currentTrack;
            audioElement.currentTime = 0;
            audioElement.play().catch(() => console.log("Autoplay blocked"));
        }
    };
    window.switchToHomeMusic = function() {
        if (currentTrack !== playlist.home) {
            currentTrack = playlist.home;
            audioElement.src = currentTrack;
            audioElement.currentTime = 0;
            audioElement.play().catch(() => console.log("Autoplay blocked"));
        }
    };
    window.playSelectSound = function() { selectSound.play(); };
    window.playSubmitSound = function() { submitSound.play(); };
    window.playCorrectSound = function() { correctSound.play(); };
    window.playRoundEndSound = function() { roundEndSound.play(); };
});