# Chama Mobile App

A React Native mobile application for managing chama (investment group) activities.

## Features

- **Dashboard**: View contribution stats and recent activities
- **Contributions**: Make M-Pesa contributions to your chama
- **Loans**: Request and track loan applications
- **Discussions**: Participate in group discussions
- **Activities**: View recent chama activities

## Setup

### Prerequisites

- Node.js (v16 or higher)
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

### Installation

1. Install dependencies:
```bash
npm install
```

2. For Android:
```bash
npx react-native run-android
```

3. For iOS:
```bash
cd ios && pod install && cd ..
npx react-native run-ios
```

## API Configuration

Update the API base URL in `src/services/api.js`:

- Android Emulator: `http://10.0.2.2:5000/api`
- iOS Simulator: `http://localhost:5000/api`
- Physical Device: `http://YOUR_COMPUTER_IP:5000/api`

## Backend Integration

This app connects to the Flask backend server. Ensure the backend is running on port 5000 with the following endpoints:

- `POST /api/login` - User authentication
- `GET /api/dashboard` - Dashboard data
- `POST /api/contribute` - Make contributions
- `GET /api/loans` - Get user loans
- `POST /api/loans/request` - Request new loan
- `GET /api/discussions` - Get discussions
- `POST /api/discussions/create` - Create discussion
- `GET /api/activities` - Get recent activities

## Demo Credentials

- Admin: `admin/admin`
- User: `user/user`