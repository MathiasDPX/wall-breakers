let videosWithControls = [];

window.addEventListener("beforeprint", () => {
    videosWithControls = [...document.querySelectorAll("video")]
        .filter(video => video.controls);

    videosWithControls.forEach(video => {
        video.controls = false;
    });
});

window.addEventListener("afterprint", () => {
    videosWithControls.forEach(video => {
        video.controls = true;
    });

    videosWithControls = [];
});