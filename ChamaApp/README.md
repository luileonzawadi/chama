# Chama Mobile App - React Native

A complete mobile application for Chama management with M-Pesa integration.

## Features ✅

- 🔐 **User Authentication** - Login with username/password
- 📊 **Dashboard** - View stats and recent activity
- 💰 **M-Pesa Contributions** - Make payments directly from mobile
- 🏦 **Loan Management** - View loan applications and status
- 💬 **Community Discussions** - Read community posts
- 📅 **Activities** - View upcoming chama events
- 📱 **Native Mobile UI** - Optimized for mobile devices

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- React Native CLI
- Android Studio (for Android)
- Xcode (for iOS - Mac only)

### Installation

1. **Install dependencies:**
```bash
cd ChamaApp
npm install
```

2. **Install iOS dependencies (Mac only):**
```bash
cd ios && pod install && cd ..
```

3. **Start Metro bundler:**
```bash
npm start
```

4. **Run on Android:**
```bash
npm run android
```

5. **Run on iOS (Mac only):**
```bash
npm run ios
```

## Backend Setup

Make sure your Flask backend is running:
```bash
cd ../
python fixed_app.py
```

The app connects to:
- Android Emulator: `http://10.0.2.2:5000/api`
- iOS Simulator: `http://localhost:5000/api`

## Login Credentials

- **Admin:** `admin` / `admin`
- **User:** `user` / `user`

## App Structure

```
ChamaApp/
├── src/
│   ├── screens/
│   │   ├── LoginScreen.js
│   │   ├── DashboardScreen.js
│   │   ├── ContributeScreen.js
│   │   ├── LoansScreen.js
│   │   ├── DiscussionsScreen.js
│   │   └── ActivitiesScreen.js
│   └── services/
│       └── api.js
├── App.js
└── package.json
```

## Key Features

### 🔐 Authentication
- Secure login with backend API
- Session management
- Auto-redirect on success

### 📊 Dashboard
- Real-time stats display
- Recent contributions
- Loan status overview
- Pull-to-refresh functionality

### 💰 M-Pesa Integration
- Direct mobile payments
- Phone number validation
- Payment confirmation
- Error handling

### 📱 Mobile-First Design
- Native navigation
- Touch-friendly interface
- Responsive layouts
- Material Design icons

## API Endpoints Used

- `POST /api/login` - Authentication
- `GET /api/dashboard` - Dashboard data
- `POST /api/contribute` - M-Pesa payments
- `GET /api/loans` - Loan information
- `GET /api/discussions` - Community posts
- `GET /api/activities` - Upcoming events

## Development Notes

- Uses React Navigation for screen management
- Axios for API communication
- Material Icons for consistent UI
- Pull-to-refresh on all data screens
- Error handling with user-friendly alerts

## Next Steps

1. **Test on real devices**
2. **Add push notifications**
3. **Implement offline support**
4. **Add biometric authentication**
5. **Build and distribute app**

Your Chama mobile app is ready! 🚀