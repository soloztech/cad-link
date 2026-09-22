// SPDX-License-Identifier: LGPL-3.0-or-later
// Standalone iframe adapter. Deliberately independent of Odoo asset bundles.
import "../lib/model-viewer/4.3.1/model-viewer.min.js";

const model = document.getElementById("cad-model");
const status = document.getElementById("cad-viewer-status");
const reset = document.getElementById("cad-reset");
const fullscreen = document.getElementById("cad-fullscreen");
const panel = document.getElementById("cad-viewer-panel");
// Literal QWeb text nodes are translated by Odoo before this standalone script
// runs, so no backend translation assets or additional RPC calls are required.
const message = (key) => document.getElementById("cad-message-" + key).textContent.trim();
const fullscreenLabel = fullscreen.textContent;

model.addEventListener("load", () => {
    reset.disabled = false;
    status.textContent = message("ready");
    status.className = "";
});
model.addEventListener("error", () => {
    reset.disabled = true;
    status.textContent = message("error");
    status.className = "error";
});
reset.addEventListener("click", () => {
    model.cameraOrbit = "0deg 75deg auto";
    model.cameraTarget = "auto auto auto";
    model.fieldOfView = "auto";
    model.jumpCameraToGoal();
});
fullscreen.hidden = !document.fullscreenEnabled;
fullscreen.addEventListener("click", async () => {
    try {
        if (document.fullscreenElement) {
            await document.exitFullscreen();
        } else {
            await panel.requestFullscreen();
        }
    } catch {
        status.textContent = message("fullscreen-error");
    }
});
document.addEventListener("fullscreenchange", () => {
    fullscreen.textContent = document.fullscreenElement ? message("fullscreen-exit") : fullscreenLabel;
});
// Each click/refresh creates a new iframe. Bypass the renderer's URL cache too;
// the endpoint reads current share contents and always returns no-store.
model.src = model.dataset.modelUrl + "&v=" + Date.now();
