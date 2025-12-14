# Server Quick Start

## On iMac Server (3 Simple Steps):

### 1. Create Marker File
```bash
touch ~/Desktop/SERVER
```
That's it - just an empty file named `SERVER` on Desktop.

### 2. Run Setup
```bash
cd ~/Desktop/ZoolZ
./setup_server.sh
```
This installs all requirements automatically.

### 3. Start Zoolz
```bash
./start_zoolz.sh
```

---

## What Happens:

**First Time:**
- Zoolz sees `~/Desktop/SERVER` file → "I'm on the server!"
- Creates `~/Desktop/ZoolZData/` with all subfolders
- Uses server paths for everything

**On Laptop (no SERVER file):**
- Zoolz sees no marker → "I'm on laptop"
- Uses local project folders
- No ZoolZData created

---

## After It Starts:

**Access locally:**
```
http://localhost:5001
```

**Access from anywhere (after port forward):**
```
http://your-public-ip:5001
```

**Login:**
- Username: `Zay`
- Password: `442767`

---

**That's literally it. One empty file, two commands, done.**
