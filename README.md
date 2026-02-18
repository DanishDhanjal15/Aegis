# 🛡️Aegis - IoT Security Guardian

**Aegis** is an advanced IoT network security platform that combines AI-powered device detection, real-time threat monitoring, and intelligent network protection. Built with modern web technologies, Aegis provides comprehensive visibility and control over your network infrastructure.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![React](https://img.shields.io/badge/react-18.2.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)

---

## 🎯 Features

### 🔍 **Network Discovery & Monitoring**
- **Real-time Device Scanning**: Discover all devices connected to your network
- **Automated Periodic Scans**: Configurable auto-scan intervals (1-60 minutes)
- **Device Fingerprinting**: Identify device types, OS, manufacturer, and open ports
- **Network Topology Mapping**:Visualize your network infrastructure

### 🤖 **AI-Powered Detection**
- **Machine Learning Classification**: Intelligent device type detection using Random Forest algorithms
- **OS Pattern Recognition**: Enhanced operating system identification
- **Adaptive Learning**: Models improve accuracy as they learn from your network
- **Smart Device Naming**: Automatically generates meaningful device names
- **85-95% Detection Accuracy** (after training on your network)

### 🔐 **Security Features**
- **Device Blocking**: Block suspicious or unauthorized devices
- **Panic Mode**: Emergency lockdown - block all devices instantly
- **Risk Assessment**: Automatic vulnerability scoring for each device
- **Activity Logging**: Comprehensive audit trail of all network events
- **Firebase Authentication**: Secure user authentication and authorization

### 💬 **Intelligent Chatbot Assistant**
- **Network Queries**: Ask questions about your network in natural language
- **Device Information**: Get instant details about connected devices
- **Security Recommendations**: Receive AI-powered security suggestions
- **Real-time Insights**: Interactive assistant for network management

### 📊 **Dashboard & Analytics**
- **Real-time Statistics**: Device counts, blocked devices, scan status
- **Modern UI**: Clean, responsive interface with dark/light theme support
- **Device Details**: In-depth information for each network device
- **Activity Logs**: Historical view of all network events
- **Visual Indicators**: Color-coded risk levels and device status

---

## 🏗️ Tech Stack

### Backend
- **FastAPI**: Modern, high-performance API framework
- **Python 3.8+**: Core programming language
- **Scapy**: Network packet manipulation and scanning
- **scikit-learn**: Machine learning models and AI detection
- **Firebase Admin SDK**: Authentication and real-time database
- **SQLite**: Local database for device storage
- **Pandas**: Data processing and feature extraction

### Frontend
- **React 18**: Modern UI framework
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Beautiful icon library
- **Firebase SDK**: Client-side authentication

---

## 📋 Prerequisites

Before installing Aegis, ensure you have:

- **Python 3.8 or higher**
- **Node.js 16+ and npm**
- **Administrator/Root privileges** (required for network scanning)
- **Firebase account** (for authentication features)
- **Windows, macOS, or Linux operating system**

---

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DanishDhanjal15/Aegis.git
cd aegis
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

---

## ⚙️ Configuration

### Firebase Setup

1. **Create a Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Authentication (Email/Password provider)

2. **Backend Configuration** (`backend/.env`):
   ```env
   # Firebase Admin SDK
   # Place your serviceAccountKey.json in the backend folder
   FIREBASE_PROJECT_ID=your-project-id
   ```

3. **Frontend Configuration** (`frontend/.env`):
   ```env
   VITE_FIREBASE_API_KEY=your-api-key
   VITE_FIREBASE_AUTH_DOMAIN=your-auth-domain
   VITE_FIREBASE_PROJECT_ID=your-project-id
   VITE_FIREBASE_STORAGE_BUCKET=your-storage-bucket
   VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
   VITE_FIREBASE_APP_ID=your-app-id
   ```

4. **Download Service Account Key**:
   - In Firebase Console, go to Project Settings → Service Accounts
   - Generate new private key
   - Save as `serviceAccountKey.json` in `backend/` folder

---

## 🎮 Usage

### Starting the Application

#### 1. Start Backend Server
```bash
cd backend
python main.py
```
Backend will run on `http://localhost:8000`

#### 2. Start Frontend Development Server
```bash
cd frontend
npm run dev
```
Frontend will run on `http://localhost:5173`

#### 3. Access the Application
Open your browser and navigate to `http://localhost:5173`

### First-Time Setup

1. **Create Account**: Register with email and password
2. **Login**: Authenticate through the login screen
3. **Run Initial Scan**: Click "Scan Network" to discover devices
4. **Train AI Models**: After scanning 10+ devices, train the AI models for enhanced detection
5. **Configure Auto-Scan**: Enable automatic periodic scanning if desired

---

## 📡 API Endpoints

### Devices
- `GET /api/devices` - Get all discovered devices
- `POST /api/scan` - Trigger manual network scan
- `GET /api/scan/status` - Get current scan status
- `POST /api/devices/{device_id}/block` - Toggle device block status
- `POST /api/devices/{device_id}/nickname` - Update device nickname

### Security
- `POST /api/panic` - Activate panic mode (block all devices)
- `POST /api/unlock-panic` - Deactivate panic mode

### Auto Scanner
- `POST /api/auto-scan/start` - Start automatic scanning
- `POST /api/auto-scan/stop` - Stop automatic scanning
- `GET /api/auto-scan/status` - Get auto-scan status
- `POST /api/auto-scan/interval` - Set scan interval

### AI Detection
- `POST /api/ai/train` - Train ML models
- `GET /api/ai/status` - Get AI detection status

### Chatbot
- `POST /api/chatbot` - Send message to chatbot
- `GET /api/chatbot/context` - Get network context for chatbot

### Logs
- `GET /api/logs` - Retrieve activity logs

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

---

## 🤖 AI Detection System

### How It Works

1. **Feature Extraction**: Extracts 20+ numerical features from device data
   - MAC address patterns
   - Open ports (binary features)
   - TTL values
   - Hostname patterns
   - Risk scores

2. **ML Models**: Random Forest classifiers for:
   - Device type classification
   - Operating system detection
   
3. **Training**: Automatic model training once sufficient data is collected

### Training Models

**Via API**:
```bash
POST http://localhost:8000/api/ai/train
```

**Requirements**: At least 10 devices in database

**Models are saved to**: `backend/models/`

### Detection Modes

- **Rule-Based**: ~70-80% accuracy (default, no training required)
- **ML-Enhanced**: ~85-95% accuracy (after training)

---

## 🔒 Security Best Practices

1. **Never commit sensitive files**:
   - `serviceAccountKey.json`
   - `.env` files
   - Database files (`*.db`)

2. **Use strong passwords** for Firebase authentication

3. **Run with appropriate privileges**:
   - Scanning requires admin/root privileges
   - Use sudo on Linux/macOS

4. **Keep dependencies updated**:
   ```bash
   pip install --upgrade -r requirements.txt
   npm update
   ```

5. **Review blocked devices** regularly in the dashboard

---

## 🛠️ Development

### Project Structure
```
aegis/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Main API server
│   ├── scanner.py       # Network scanning logic
│   ├── ai_detector.py   # AI/ML detection system
│   ├── chatbot.py       # Chatbot implementation
│   ├── database.py      # Database operations
│   ├── blocker.py       # Device blocking logic
│   ├── auto_scanner.py  # Auto-scan scheduler
│   ├── firebase_admin_config.py  # Firebase setup
│   └── models/          # Trained ML models
├── frontend/            # React frontend
│   └── src/
│       ├── App.jsx      # Main application
│       ├── api.js       # API client
│       ├── firebase.js  # Firebase config
│       └── components/  # React components
└── README.md
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Build frontend
cd frontend
npm run build

# Serve with backend
cd ../backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Permission Denied during scanning**
```bash
# Run with administrator privileges
# Windows: Run terminal as Administrator
# Linux/macOS: Use sudo
sudo python main.py
```

**2. Firebase Authentication Error**
- Verify `serviceAccountKey.json` is in the `backend/` folder
- Check Firebase project settings match your `.env` files
- Ensure Email/Password authentication is enabled in Firebase Console

**3. AI Models Not Training**
- Ensure you have at least 10 devices scanned
- Check `scikit-learn` is installed: `pip install scikit-learn`
- View logs for error messages

**4. Network Scan Not Detecting Devices**
- Verify you're on the same network as target devices
- Check firewall settings
- Run with elevated privileges

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

**Danish Dhanjal**
- GitHub: [@DanishDhanjal15](https://github.com/DanishDhanjal15)

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Scapy for powerful network scanning capabilities
- Firebase for authentication infrastructure
- React and Vite for the modern frontend stack
- scikit-learn for machine learning capabilities

---

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on [GitHub](https://github.com/DanishDhanjal15/Aegis/issues)
- Check existing documentation in the repository

---

## 🗺️ Roadmap

- [ ] Multi-network support
- [ ] Advanced threat detection with deep learning
- [ ] Mobile application
- [ ] Network traffic analysis
- [ ] Custom alerting rules
- [ ] Integration with external security tools
- [ ] Docker containerization
- [ ] Cloud deployment options

---

**⚠️ Disclaimer**: This tool is for network security and monitoring purposes. Always ensure you have proper authorization before scanning any network. Unauthorized network scanning may be illegal in your jurisdiction.
