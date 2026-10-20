const BACKEND_URL = "https://ai-interview-evaluator-hgjg.onrender.com/api/evaluate";

document.getElementById("submitBtn").addEventListener("click", async () => {
    const topicInput = document.getElementById("topicInput").value.trim();
    const answerInput = document.getElementById("answerInput").value.trim();
    const submitBtn = document.getElementById("submitBtn");
    const resultSection = document.getElementById("resultSection");
    const scoreDisplay = document.getElementById("scoreDisplay");
    const feedbackDisplay = document.getElementById("feedbackDisplay");

    // Empty input check
    if (!topicInput || !answerInput) {
        alert("Please enter both the interview topic and your answer before evaluating.");
        return;
    }

    // 1. Set Loading UI State
    submitBtn.innerText = "Evaluating... ⏳";
    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-50", "cursor-not-allowed");
    resultSection.classList.add("hidden");

    console.log("Initiating evaluation... Connecting to cloud server.");

    try {
        // 2. Fetch data from Render Backend
        const response = await fetch(BACKEND_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                topic: topicInput,
                transcript: answerInput, 
                user_email: "guest"
            })
        });

        if (!response.ok) {
            throw new Error(`Evaluation failed. Server responded with status: ${response.status}`);
        }

        const result = await response.json();
        console.log("Evaluation completed successfully:", result);

        // 3. Display Results dynamically
        scoreDisplay.innerText = result.evaluation.score;
        feedbackDisplay.innerText = result.evaluation.feedback;
        resultSection.classList.remove("hidden");

    } catch (error) {
        console.error("Network or Fetch Error:", error);
        alert("Connection failed. Please ensure the server is active and try again.");
    } finally {
        // 4. Reset Button State
        submitBtn.innerText = "Evaluate Answer";
        submitBtn.disabled = false;
        submitBtn.classList.remove("opacity-50", "cursor-not-allowed");
    }
});