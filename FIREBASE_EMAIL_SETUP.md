# 🔥 Firebase Email Configuration Guide

## Why Emails Aren't Sending

Firebase needs to be configured in the Firebase Console to send password reset emails. Follow these steps:

---

## ✅ Step-by-Step Setup

### 1. **Go to Firebase Console**
- Visit: https://console.firebase.google.com/
- Select your project: **aegis-project-f88c3**

### 2. **Enable Email Authentication**
- Click **"Authentication"** in the left sidebar
- Go to **"Sign-in method"** tab
- Make sure **"Email/Password"** is **ENABLED**
- Save if you made changes

### 3. **Configure Email Templates** (CRITICAL)
- Still in **Authentication** section
- Click **"Templates"** tab at the top
- You'll see templates for:
  - Password reset
  - Email address verification
  - Email address change

### 4. **Customize Password Reset Template**
- Click on **"Password reset"** template
- Click **"Edit template"** (pencil icon)
- **Customize the email** (optional):
  - From name: `Aegis Guardian`
  - Subject: `Reset Your Aegis Password`
  - Body: Customize as needed
- **IMPORTANT**: Click **"Save"** at the bottom

### 5. **Verify Your Domain (IMPORTANT)**
- Go to **"Authentication"** → **"Settings"** tab
- Scroll to **"Authorized domains"**
- Make sure these are listed:
  - `localhost`
  - `aegis-project-f88c3.firebaseapp.com`
  - Any custom domain you use
- Add domains if missing

### 6. **Check Email Provider Settings**
- In **Authentication** → **"Templates"** → **"SMTP settings"**
- Firebase uses its own email service by default (noreply@aegis-project-f88c3.firebaseapp.com)
- **No changes needed** unless you want custom email sender

---

## 🧪 Testing the Feature

### Test with a Real Email:
1. **Restart your frontend** (Ctrl+C, then `npm run dev`)
2. Go to login page: `http://localhost:5173`
3. Click **"Forgot Password?"**
4. Enter your **registered email** (must be an account you've signed up with)
5. Click **"Send Reset Link"**
6. **Check your inbox** (Gmail, Outlook, etc.)
   - **Check SPAM/JUNK folder** if not in inbox
   - Email sender: `noreply@aegis-project-f88c3.firebaseapp.com`
   - Subject: "Reset your password for [your app]"

### Expected Email:
```
Reset your password for aegis-project-f88c3

Follow this link to reset your password for your aegis-project-f88c3 account.

[Reset Password Button]

If you didn't ask to reset your password, you can ignore this email.

Your password won't change until you create a new password.
```

---

## 🔍 Debugging

### If email still doesn't arrive:

#### 1. **Check Browser Console**
- Open DevTools (F12)
- Go to "Console" tab
- Look for error messages when clicking "Send Reset Link"
- Share any red errors you see

#### 2. **Check Firebase Console Logs**
- Go to Firebase Console → **Authentication** → **Users**
- Verify the user email exists in the list
- Try with a different email if the account doesn't exist

#### 3. **Check Email Provider**
- Gmail: Check "All Mail" and "Spam"
- Outlook: Check "Junk Email"
- Wait 2-3 minutes (emails can be delayed)

#### 4. **Common Issues:**

| Issue | Solution |
|-------|----------|
| "User not found" | The email isn't registered - sign up first |
| "Network error" | Check internet connection |
| "Too many requests" | Wait 5-10 minutes before retrying |
| Email in spam | Mark as "Not Spam" and whitelist Firebase domain |

---

## 🎯 Quick Test Checklist

- [ ] Firebase Authentication is enabled
- [ ] Email/Password sign-in method is enabled
- [ ] Email templates are saved in Firebase Console
- [ ] Test email is a **registered account**
- [ ] Checked spam/junk folders
- [ ] Waited 2-3 minutes for email delivery
- [ ] Browser console shows no errors
- [ ] Internet connection is working

---

## 🆘 Still Not Working?

### Option 1: Use Firebase Authentication Emulator (Advanced)
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize emulator
firebase init emulators

# Start emulator
firebase emulators:start
```

### Option 2: Check Email Deliverability
- Firebase's default email service sometimes gets flagged
- Consider setting up a custom SMTP provider:
  - SendGrid
  - Mailgun
  - AWS SES

### Option 3: Verify in Firebase Console
1. Go to **Authentication** → **Users**
2. Click on a user
3. Click **"Send password reset email"** manually
4. Check if that email arrives

---

## 📝 Notes

- Firebase password reset emails are **automatic** once configured
- Emails come from: `noreply@[YOUR-PROJECT-ID].firebaseapp.com`
- The reset link expires after **1 hour**
- Users can request multiple reset emails
- Each reset link is **single-use** (can't be reused)

---

## ✅ Success Indicators

When working correctly, you'll see:
1. ✅ Success message: "Password reset email sent! Check your inbox"
2. ✅ Console log: "Password reset email sent successfully to: [email]"
3. ✅ Email arrives within 1-3 minutes
4. ✅ Reset link works when clicked

---

## 🔐 Security Notes

- Firebase handles all security automatically
- Reset tokens are time-limited (1 hour)
- One-time use links (can't reuse after password change)
- Secure Firebase-hosted reset page
- No passwords sent via email

---

Need more help? Check:
- Firebase Docs: https://firebase.google.com/docs/auth/web/manage-users#send_a_password_reset_email
- Firebase Console: https://console.firebase.google.com/

