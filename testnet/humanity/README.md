---

# 🚀 Auto Daily Claim $RWT Humanity Protocol Bot  

### ✅ Automate your $RWT reward claims effortlessly!  

## 📌 Introduction  
This bot automates the daily claiming of $RWT rewards from the **Humanity Protocol**, allowing users to manage multiple wallets efficiently. It is designed to be **easy to set up, secure, and reliable**.  

---

## 🛠️ Getting Started  

Follow these simple steps to set up and run the bot on your local machine.  

### 1️⃣ Clone the Repository  
First, clone this repository to your local machine using Git:  

```bash
git clone https://github.com/rbbaprianto/humanity-protocol.git
```

### 2️⃣ Navigate to the Project Directory  
Move into the cloned project folder:  

```bash
cd humanity-protocol
```

### 3️⃣ Create a `private_keys.txt` File  
Create a file named `private_keys.txt` in the **root directory** of the project. Add your **wallet private keys**, each on a new line, like this:  

```txt
private_key_1
private_key_2
private_key_3
...
```

⚠️ **Keep this file private!** Never share your private keys with anyone.  

---

## 🔧 Installation  

### 4️⃣ Install Python & Virtual Environment (Linux Users)  
Ensure you have **Python 3** installed. If not, install it using:  

```bash
sudo apt-get install python3 python3-venv
```

Then, create and activate a virtual environment:  

```bash
python3 -m venv venv
source venv/bin/activate
```

### 5️⃣ Install Dependencies  
Install all required Python packages:  

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Bot  

Once everything is set up, you can run the bot with:  

```bash
python3 bot.py
```

The bot will automatically:  
✅ Connect to the **Humanity Protocol**  
✅ Load your **wallets**  
✅ Claim **$RWT rewards** daily  
✅ Handle **multiple wallets** in one session  

---

## 📌 Additional Notes  

- The bot **runs automatically** and claims rewards every **6 hours**.  
- If you encounter any issues, check the logs for error messages.  
- Future improvements may include **auto-restart, error handling, and performance optimizations**.  

🚀 **Enjoy automated $RWT claiming and maximize your rewards effortlessly!**  

---
