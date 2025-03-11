// static/music.js
document.addEventListener("DOMContentLoaded", function() {
    // Playlist array
    const playlist = [
        '/static/music.mp3',
        '/static/music1.mp3',
        '/static/music2.mp3',
        '/static/music3.mp3'
    ];
    let currentTrackIndex = parseInt(sessionStorage.getItem("musicTrackIndex")) || 0;

    // Initialize audio element
    const audioElement = new Audio(playlist[currentTrackIndex]);
    audioElement.loop = false; // Disable loop since we have a playlist

    // DOM elements
    const musicControlBtn = document.getElementById("music-control-btn");
    const musicPlayer = document.getElementById("music-player");
    const playBtn = document.getElementById("play-btn");
    const pauseBtn = document.getElementById("pause-btn");
    const skipBtn = document.getElementById("skip-btn");
    const muteBtn = document.getElementById("mute-btn");

    // Load saved state from sessionStorage
    const savedState = {
        isPlaying: sessionStorage.getItem("musicIsPlaying") === "true",
        currentTime: parseFloat(sessionStorage.getItem("musicCurrentTime")) || 0,
        isMuted: sessionStorage.getItem("musicIsMuted") === "true"
    };

    // Apply saved state
    audioElement.currentTime = savedState.currentTime;
    audioElement.muted = savedState.isMuted || true; // Muted by default until interaction
    muteBtn.classList.toggle("btn-muted", audioElement.muted);

    if (savedState.isPlaying) {
        audioElement.play().catch(() => console.log("Autoplay blocked."));
    }

    // Toggle music player visibility
    musicControlBtn.addEventListener("click", function() {
        musicPlayer.classList.toggle("active");
    });

    // Play audio
    playBtn.addEventListener("click", function() {
        audioElement.play();
        sessionStorage.setItem("musicIsPlaying", "true");
        muteBtn.classList.remove("btn-muted");
        audioElement.muted = false;
        sessionStorage.setItem("musicIsMuted", "false");
    });

    // Pause audio
    pauseBtn.addEventListener("click", function() {
        audioElement.pause();
        sessionStorage.setItem("musicIsPlaying", "false");
    });

    // Skip to next track
    skipBtn.addEventListener("click", function() {
        currentTrackIndex = (currentTrackIndex + 1) % playlist.length;
        audioElement.src = playlist[currentTrackIndex];
        audioElement.currentTime = 0;
        audioElement.play();
        sessionStorage.setItem("musicTrackIndex", currentTrackIndex);
        sessionStorage.setItem("musicIsPlaying", "true");
        sessionStorage.setItem("musicCurrentTime", "0");
        muteBtn.classList.remove("btn-muted");
        audioElement.muted = false;
        sessionStorage.setItem("musicIsMuted", "false");
    });

    // Mute/Unmute toggle
    muteBtn.addEventListener("click", function() {
        audioElement.muted = !audioElement.muted;
        sessionStorage.setItem("musicIsMuted", audioElement.muted);
        muteBtn.classList.toggle("btn-muted", audioElement.muted);
    });

    // Save current time periodically
    audioElement.addEventListener("timeupdate", function() {
        sessionStorage.setItem("musicCurrentTime", audioElement.currentTime);
    });

    // Automatically skip to next track when current one ends
    audioElement.addEventListener("ended", function() {
        currentTrackIndex = (currentTrackIndex + 1) % playlist.length;
        audioElement.src = playlist[currentTrackIndex];
        audioElement.currentTime = 0;
        audioElement.play();
        sessionStorage.setItem("musicTrackIndex", currentTrackIndex);
        sessionStorage.setItem("musicIsPlaying", "true");
        sessionStorage.setItem("musicCurrentTime", "0");
    });

    // Unmute and attempt play on first user interaction
    document.addEventListener("click", function() {
        if (audioElement.muted) {
            audioElement.muted = false;
            sessionStorage.setItem("musicIsMuted", "false");
            if (savedState.isPlaying || !sessionStorage.getItem("musicIsPlaying")) {
                audioElement.play().catch(() => console.log("Autoplay blocked."));
                sessionStorage.setItem("musicIsPlaying", "true");
            }
        }
    }, { once: true });

    // Handle page unload to save final state
    window.addEventListener("beforeunload", function() {
        sessionStorage.setItem("musicIsPlaying", !audioElement.paused);
        sessionStorage.setItem("musicCurrentTime", audioElement.currentTime);
        sessionStorage.setItem("musicIsMuted", audioElement.muted);
        sessionStorage.setItem("musicTrackIndex", currentTrackIndex);
    });
});