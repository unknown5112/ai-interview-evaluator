// --- 1. DARK/LIGHT MODE LOGIC ---
const themeToggleBtn = document.getElementById('theme-toggle');
if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

themeToggleBtn.addEventListener('click', () => {
  document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
});

// --- 2. SUPABASE AUTH SETUP ---
// YAHAN APNI ASLI DETAILS DAALNA
const SUPABASE_URL = 'https://zkzfelzbcskmzgyfynjz.supabase.co';
const SUPABASE_KEY = 'sb_publishable_TEvCsRbd9Zid9wYsbJDRSA_0Bw9qdhd';
const BACKEND_URL = 'https://ai-interview-evaluator-hgjg.onrender.com'; // Tera render wala link

const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

let currentUserEmail = null;

// UI Elements
const authSection = document.getElementById('auth-section');
const userSection = document.getElementById('user-section');
const emailDisplay = document.getElementById('user-email-display');
const pastScoresContainer = document.getElementById('past-scores-container');
const scoresList = document.getElementById('scores-list');

// Listen for Login/Logout state changes
supabase.auth.onAuthStateChange((event, session) => {
    if (session) {
        currentUserEmail = session.user.email;
        authSection.classList.add('hidden');
        userSection.classList.remove('hidden');
        emailDisplay.innerText = currentUserEmail;
        pastScoresContainer.classList.remove('hidden');
        fetchPastScores(currentUserEmail); 
    } else {
        currentUserEmail = null;
        authSection.classList.remove('hidden');
        userSection.classList.add('hidden');
        pastScoresContainer.classList.add('hidden');
    }
});

// Login / Sign Up Logic (Email & Password)
document.getElementById('login-btn').addEventListener('click', async () => {
    const email = document.getElementById('email-input').value;
    const password = document.getElementById('password-input').value;
    
    if(!email || !password) return alert("Please enter both email and password.");

    const { data, error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) {
        // Agar account nahi hai, toh sign up try karo
        const { data: signUpData, error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) {
            alert("Error: " + signUpError.message);
        } else {
            alert("Signup successful! Please check your email to verify.");
        }
    }
});

// Google OAuth Login
document.getElementById('google-login-btn').addEventListener('click', async () => {
    const { error } = await supabase.auth.signInWithOAuth({ provider: 'google' });
    if (error) alert("Google Login Error: " + error.message);
});

// Logout Logic
document.getElementById('logout-btn').addEventListener('click', async () => {
    await supabase.auth.signOut();
    scoresList.innerHTML = ''; 
});

// --- 3. FETCH PAST SCORES LOGIC ---
async function fetchPastScores(email) {
    try {
        scoresList.innerHTML = '<p class="text-indigo-500 animate-pulse">Loading your previous interview scores...</p>';
        const response = await fetch(`${BACKEND_URL}/api/scores/${email}`);
        
        if (!response.ok) throw new Error("Failed to fetch scores");
        
        const result = await response.json();
        scoresList.innerHTML = ''; 
        
        if (result.data && result.data.length > 0) {
            result.data.forEach(item => {
                const scoreCard = document.createElement('div');
                scoreCard.className = "p-4 border border-gray-200 dark:border-slate-700 rounded-lg bg-gray-50 dark:bg-slate-800";
                scoreCard.innerHTML = `
                    <h3 class="font-bold text-lg text-indigo-600 dark:text-indigo-400">${item.topic}</h3>
                    <p class="text-green-500 font-bold text-xl mt-1">Score: ${item.score}/10</p>
                    <p class="text-sm mt-3 text-gray-700 dark:text-gray-300">${item.feedback}</p>
                `;
                scoresList.appendChild(scoreCard);
            });
        } else {
            scoresList.innerHTML = '<p class="text-gray-500">No past interviews found. Start your first evaluation!</p>';
        }
    } catch (error) {
        console.error("Error fetching scores:", error);
        scoresList.innerHTML = '<p class="text-red-500">Failed to load scores. Please try again later.</p>';
    }
}

// --- 4. MAIN EVALUATION LOGIC ---
document.getElementById('evaluate-btn').addEventListener('click', async () => {
    const topic = document.getElementById('topic').value;
    const transcript = document.getElementById('transcript').value;
    
    if (!topic || !transcript) return alert("Please enter both topic and answer!");

    // UI Updates during loading
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('result-section').classList.add('hidden');
    document.getElementById('evaluate-btn').disabled = true;
    document.getElementById('evaluate-btn').classList.add('opacity-50', 'cursor-not-allowed');

    try {
        const response = await fetch(`${BACKEND_URL}/api/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                transcript: transcript,
                user_email: currentUserEmail || "anonymous@user.com" // Logs to anonymous if not logged in
            })
        });

        if (!response.ok) throw new Error("Server Error: " + response.statusText);

        const data = await response.json();
        
        // Show Results
        document.getElementById('score').innerText = data.evaluation.score;
        document.getElementById('feedback').innerText = data.evaluation.feedback;
        document.getElementById('result-section').classList.remove('hidden');

        // Agar user logged in hai, toh past scores ki list dobara refresh kar do
        if (currentUserEmail) {
            fetchPastScores(currentUserEmail);
        }

    } catch (error) {
        alert("An error occurred during evaluation. Please check console.");
        console.error(error);
    } finally {
        // Reset UI
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('evaluate-btn').disabled = false;
        document.getElementById('evaluate-btn').classList.remove('opacity-50', 'cursor-not-allowed');
    }
});