# BlockMesh Network AutoBot

Multi-account automation tool for BlockMesh Network with proxy support.

## Features

- ✅ Multi-account support (load from `query.txt`)
- 🔒 Proxy support (SOCKS4/5, HTTP/HTTPS)
- ⏱️ Automatic uptime reporting every 5 minutes
- 📝 Detailed logging with timestamps
- 🎨 Colorized console output
- 🔄 Auto-reconnect on failure

## Requirements

- Python 3.6+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository:
```bash
svn export https://github.com/robprian/rob-drop/trunk/telegram_blockmesh
cd BlockMesh-AutoBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Prepare your accounts in `query.txt` (format: `email|password`):
```
user1@domain.com|password123
user2@domain.com|mypassword
```

2. Prepare your proxies in `proxies.txt` (format: `protocol://user:pass@ip:port` or `protocol://ip:port`):
```
socks5://user:pass@1.2.3.4:1080
http://5.6.7.8:3128
```

## Usage

Run the script:
```bash
python blockmesh_autobot.py
```

Keyboard shortcuts:
- `Ctrl+C` - Graceful shutdown

## Log Format Example

```
[23:10:40][user1@domain.com] Login successfully | 1.2.3.4
[23:10:41][user2@domain.com] Login successfully | 5.6.7.8
[23:15:40][user1@domain.com] PING successfully | 1.2.3.4
[23:15:41][user2@domain.com] PING successfully | 5.6.7.8
```

## Troubleshooting

**Login failed errors:**
- Verify your credentials in `query.txt`
- Check proxy connectivity
- Ensure BlockMesh service is available

**Proxy connection issues:**
- Test proxies with other tools
- Verify proxy format in `proxies.txt`
- Try different proxy protocols

## Disclaimer

This tool is provided for educational purposes only. Use at your own risk. The developer is not responsible for any account restrictions or violations of BlockMesh's Terms of Service that may result from using this tool.

## License

MIT License - See [LICENSE](LICENSE) file for details.
