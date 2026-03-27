/**
 * firebase-init.js
 * ─────────────────────────────────────────────────────────────
 * Single source of Firebase initialisation for ALL dashboard pages.
 *
 * Config is fetched at runtime from the app.py backend endpoint
 * (/api/firebase-config), which reads it from service_account_key.json.
 *
 * ⚠️  app.py MUST be running (python app.py) before opening any page.
 *
 * Usage in any HTML page (type="module"):
 *
 *   import { initFirebase } from "./firebase-init.js";
 *   const { app, auth, db, config } = await initFirebase();
 * ─────────────────────────────────────────────────────────────
 */

import { initializeApp }  from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getAuth }        from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import { getFirestore }   from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

// ── Where app.py is running ───────────────────────────────────
// Change this if you deploy app.py to a server.
// When serving through app.py locally, keep as-is.
const CONFIG_ENDPOINT = "/api/firebase-config";

// ─────────────────────────────────────────────────────────────
let _firebaseApp    = null;
let _firebaseCache  = null;

/**
 * Fetch Firebase client config from the app.py backend.
 * Result is cached so only one network request is ever made.
 */
async function fetchConfig() {
  if (_firebaseCache) return _firebaseCache;

  const res = await fetch(CONFIG_ENDPOINT);
  if (!res.ok) {
    throw new Error(
      `[FIRO] Could not load Firebase config from ${CONFIG_ENDPOINT} — ` +
      `HTTP ${res.status}. Is app.py running?`
    );
  }

  _firebaseCache = await res.json();
  return _firebaseCache;
}

/**
 * Initialize Firebase once and return shared instances.
 * Safe to call multiple times — returns the same instances.
 *
 * @returns {{ app, auth, db, config }}
 */
export async function initFirebase() {
  const config = await fetchConfig();

  if (!_firebaseApp) {
    _firebaseApp = initializeApp(config);
  }

  return {
    app:    _firebaseApp,
    auth:   getAuth(_firebaseApp),
    db:     getFirestore(_firebaseApp),
    config,                             // includes projectId, etc.
  };
}
