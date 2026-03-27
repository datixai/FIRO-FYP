// --- Mandatory Imports (using SDK v11.6.1) ---
import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getAuth, signInAnonymously, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import { getFirestore, setLogLevel } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-database.js";

// --- Mandatory Variable Setup ---
// We must use the global variables provided by the environment for configuration.
const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');
const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;

// --- Initialize Firebase Services ---
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const firestore = getFirestore(app);
const rtdb = getDatabase(app); // Renamed to rtdb to distinguish from the db variable in the original code

// --- Authentication Logic (Mandatory) ---
async function authenticateAndInitialize() {
    try {
        if (initialAuthToken) {
            // Use custom token if provided (standard for this environment)
            await signInWithCustomToken(auth, initialAuthToken);
            console.log("Authenticated successfully via custom token.");
        } else {
            // Fallback to anonymous sign-in if no token is available
            await signInAnonymously(auth);
            console.log("Authenticated anonymously.");
        }

        // Set Firestore log level for debugging
        setLogLevel('debug');

        // Export the initialized services for use elsewhere in your application
        window.app = app;
        window.auth = auth;
        window.firestore = firestore;
        window.rtdb = rtdb;

        console.log("Firestore instance initialized:", firestore);
        console.log("Realtime Database instance initialized:", rtdb);

    } catch (error) {
        // Log errors without using alert()
        console.error("Firebase Initialization or Authentication Failed:", error.message);
    }
}

// Start the initialization process
authenticateAndInitialize();
