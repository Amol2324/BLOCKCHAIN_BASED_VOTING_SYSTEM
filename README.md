# 🗳 VoteChain - A Simple and Secure Online Voting System

**VoteChain** is a digital voting system built using Python, Flask, and blockchain technology. It allows users (voters) to register, log in, and vote online — securely and transparently.

The core idea behind VoteChain is to prevent vote tampering by using blockchain, where each vote is recorded as a block that cannot be changed once added.

---

##  What This Project Does

-  Lets voters **register and log in** securely  
-  Allows users to **cast one vote** only  
-  Uses **blockchain** to store every vote securely  
-  Gives admins a simple **dashboard to view results**  
-  Makes sure **nobody can change or delete votes**

---

## 🔧 Tech Stack (What We Used)

| Layer       | Technology Used       | Purpose                                      |
|------------|------------------------|----------------------------------------------|
| Frontend   | HTML, CSS, JavaScript  | User interface for voting and admin access   |
| Backend    | Python + Flask         | Handles logic, APIs, and requests            |
| Blockchain | Python (custom code)   | Stores votes securely, block by block        |
| Database   | SQLite                 | Stores user info (name, voter ID, password)  |
| Security   | SHA-256                | Protects passwords and vote integrity        |

##  How It Works

1. **User registers** on the platform with a name, voter ID, and password  
2. **User logs in** and casts their vote  
3. The vote is converted into a **block** and added to the blockchain  
4. The admin can **view results and verify** that the blockchain is not tampered
5. 
