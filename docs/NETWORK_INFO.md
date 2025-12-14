# ZoolZ Network Configuration

## Your Network Details

### Server (iMac):
- **Local IP:** `10.0.0.11` (use this from laptop on same network)
- **Public IP:** `71.60.55.85` (use this from anywhere on internet)
- **Port:** `5001`

---

## How to Access ZoolZ

### From Laptop (Same Network):
```
http://10.0.0.11:5001
```
**Use this when you're at home on the same WiFi as the iMac.**

Login:
- Username: `Zay`
- Password: `442767`

---

### From Internet (Anywhere):
```
http://71.60.55.85:5001
```
**Use this when you're away from home (coffee shop, etc.).**

**Requirements:**
- Port forwarding must be configured on your router
- Forward external port `5001` → internal `10.0.0.11:5001`
- You mentioned you already did this ✅

---

## Testing Access

### 1. Test Local Access (On iMac):
```
http://localhost:5001
```
Should work immediately after server starts.

### 2. Test LAN Access (From Laptop):
```
http://10.0.0.11:5001
```
Should work when laptop is on same WiFi.

### 3. Test Internet Access (From Phone on Cellular):
```
http://71.60.55.85:5001
```
Only works if port forwarding is configured correctly.

---

## Troubleshooting

### Can't access from laptop:
1. Make sure both devices on same WiFi
2. Check iMac firewall allows port 5001
3. Verify ZoolZ is running: `./monitor_server.sh`

### Can't access from internet:
1. Verify port forwarding: External 5001 → 10.0.0.11:5001
2. Test with phone on cellular (not WiFi)
3. Check if public IP changed (ISPs sometimes rotate IPs)

### Find current public IP:
```bash
curl ifconfig.me
```
If it's not `71.60.55.85`, update your bookmarks.

---

## Security Notes

- **Username/Password:** Currently hardcoded as `Zay`/`442767`
- **HTTPS:** Not configured (uses HTTP)
- **Recommendation:** For internet access, consider:
  - Changing default password
  - Setting up HTTPS with Let's Encrypt
  - Using a VPN instead of port forwarding

---

## Dynamic DNS (Optional)

If your public IP changes frequently, consider using:
- **No-IP** (free dynamic DNS)
- **DuckDNS** (free)
- **Cloudflare Tunnel** (free, no port forwarding needed)

This gives you a permanent URL like `zoolz.ddns.net` instead of remembering IP addresses.

---

**YOU'RE ALL SET!** Your network is already configured correctly. 🚀
