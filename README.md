# vote-shield

> Secure voting system backend  
> v0.1 | Django 4.2 | Python 3.10  

## team  
- **Lead**: [Soe Pyae Pyae Phyo ]  
- **Associates**:  
  - Mya Thinzar Aung 
  - Min Thu Khaing 

## setup  
1. `git clone https://github.com/[repo].git`  
2. `pip install -r requirements.txt`  
3. Configure `.env` (ref: .env.sample)  
4. `python manage.py migrate`  

## core functions  
- `/admin` → Poll management  
- `/api/votes` → Voting endpoints  
- `/analytics` → Results processing  

## auth specs  
- JWT tokens (72hr expiry)  
- IP rate-limiting (20req/min)  
- PBKDF2 password hashing  

## db schema  
```sql
polls (id, title, start/end_dt, is_public)  
candidates (id, poll_id, name, photo_url)  
votes (id, poll_id, user_hash, timestamp)  
