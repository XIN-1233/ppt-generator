/* AI PPT Generator - Frontend Logic */

(function () {
    "use strict";

    // State
    var isGenerating = false;

    // DOM elements
    var form = document.getElementById("ppt-form");
    var generateBtn = document.getElementById("generate-btn");
    var statusDiv = document.getElementById("status");
    var statusText = document.getElementById("status-text");
    var errorDiv = document.getElementById("error");

    // Status messages for UX
    var statusMessages = [
        "AI is crafting your slides...",
        "Structuring the content...",
        "Designing the layout...",
        "Almost there...",
    ];
    var statusInterval = null;

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (isGenerating) return;

        hideError();

        // Collect form data
        var formData = {
            topic: document.getElementById("topic").value.trim(),
            slide_count: parseInt(
                document.getElementById("slide_count").value, 10
            ),
            style: document.getElementById("style").value,
            language: document.getElementById("language").value,
            tone: document.getElementById("tone").value,
            audience:
                document.getElementById("audience").value.trim() || null,
            include_speaker_notes:
                document.getElementById("include_speaker_notes").checked,
            include_emojis:
                document.getElementById("include_emojis").checked,
        };

        // Client-side validation
        if (formData.topic.length < 2) {
            showError(
                "Please enter a meaningful topic (at least 2 characters)."
            );
            return;
        }

        // Enter loading state
        setLoading(true);
        startStatusRotation();

        fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        })
            .then(function (response) {
                if (!response.ok) {
                    return response
                        .json()
                        .catch(function () {
                            return { detail: "Server error (" + response.status + ")" };
                        })
                        .then(function (errData) {
                            throw new Error(
                                errData.detail ||
                                    "Server error (" + response.status + ")"
                            );
                        });
                }

                // Extract filename from Content-Disposition header
                var disposition = response.headers.get("Content-Disposition");
                var filename = "presentation.pptx";
                if (disposition) {
                    var match = disposition.match(
                        /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
                    );
                    if (match && match[1]) {
                        filename = match[1].replace(/['"]/g, "");
                    }
                }

                return response.blob().then(function (blob) {
                    return { blob: blob, filename: filename };
                });
            })
            .then(function (result) {
                if (!result) return;

                // Trigger browser download
                var url = window.URL.createObjectURL(result.blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = result.filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                statusText.textContent = "Download complete!";
                stopStatusRotation();
                setTimeout(function () {
                    setLoading(false);
                }, 1500);
            })
            .catch(function (err) {
                showError(err.message);
                setLoading(false);
                stopStatusRotation();
            });
    });

    // --- Helpers ---

    function setLoading(loading) {
        isGenerating = loading;
        generateBtn.disabled = loading;
        statusDiv.classList.toggle("hidden", !loading);

        if (loading) {
            generateBtn.textContent = "Generating...";
        } else {
            generateBtn.textContent = "Generate Presentation";
            statusText.textContent = "AI is crafting your slides...";
        }
    }

    function startStatusRotation() {
        var i = 0;
        statusInterval = setInterval(function () {
            i = (i + 1) % statusMessages.length;
            statusText.textContent = statusMessages[i];
        }, 3000);
    }

    function stopStatusRotation() {
        if (statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove("hidden");
    }

    function hideError() {
        errorDiv.classList.add("hidden");
    }
})();
