// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.0/firebase-app.js";
import { getAuth } from "https://www.gstatic.com/firebasejs/10.7.0/firebase-auth.js";
import { getDatabase } from "https://www.gstatic.com/firebasejs/10.7.0/firebase-database.js";
import { getAnalytics } from "https://www.gstatic.com/firebasejs/10.7.0/firebase-analytics.js";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBoOK4eiWOxOOsSvzHe3ekW5MNi_fTq7fQ",
  authDomain: "glade-b8506.firebaseapp.com",
  databaseURL: "https://glade-b8506-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "glade-b8506",
  storageBucket: "glade-b8506.firebasestorage.app",
  messagingSenderId: "588242997541",
  appId: "1:588242997541:web:329a6a62248e36b6c58acc",
  measurementId: "G-KS86XBZ79Y"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
const auth = getAuth(app);

// Initialize Realtime Database and get a reference to the service
const database = getDatabase(app);

// Initialize Analytics and get a reference to the service
const analytics = getAnalytics(app);

console.log('✅ Firebase initialized successfully');
console.log('✅ Auth:', auth ? 'Ready' : 'Error');
console.log('✅ Database:', database ? 'Ready' : 'Error');
console.log('✅ Analytics:', analytics ? 'Ready' : 'Error');

// Export for use in other modules
export { app, auth, database, analytics };