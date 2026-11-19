# Vercel-এ লাইভ করার গাইড (ফ্রি)

ওয়েবসাইট চলে **Vercel**-এ। ডাটাবেজও **Vercel-এর ভেতর থেকেই** এক ক্লিকে চালু হয়: Storage → Postgres (Neon)।
আপলোড করা ছবি সেই ডাটাবেজেই থাকে, তাই আলাদা MySQL, Neon বা Cloudinary অ্যাকাউন্ট লাগে না।

```
GitHub (কোড) ──► Vercel (ওয়েবসাইট + ডাটাবেজ + ছবি)
```

আপনার কম্পিউটারে সাইট আগের মতোই **SQLite** (`portfolio.sqlite3`) আর `media/` ফোল্ডারে চলবে।

---

## ধাপ ১ — Vercel-এ প্রজেক্ট Import
1. https://vercel.com-এ **Continue with GitHub** দিয়ে লগইন করুন।
2. **Add New… → Project** চাপুন, তারপর `engektiar/ektiarsoft`-এর পাশে **Import** চাপুন।
3. **Framework Preset:** `Other`। অন্য কিছু বদলাবেন না।
4. **Environment Variables**-এ একটা যোগ করুন:
   - Name: `SECRET_KEY`
   - Value: একটা লম্বা র‍্যান্ডম লেখা। বানাতে টার্মিনালে চালান: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
5. **Deploy** চাপুন।
   প্রথমবার Error আসবে ("No database…")। এটা স্বাভাবিক, কারণ ডাটাবেজ এখনো চালু হয়নি।

## ধাপ ২ — ডাটাবেজ চালু (এক ক্লিক)
1. Vercel-এ প্রজেক্ট খুলুন → উপরের মেনুতে **Storage**।
2. **Create Database** → **Neon (Serverless Postgres)** → **Continue**।
3. Region: **Singapore (sin1)**, Plan: **Free** → **Create**।
4. **Connect Project**-এ আপনার প্রজেক্ট বেছে নিন। Production, Preview আর Development, তিনটাতেই টিক রাখুন।
   Vercel নিজে থেকে `DATABASE_URL` সেট করে দেবে, আপনাকে কিছু কপি করতে হবে না।

## ধাপ ৩ — আপনার এখনকার সাইট ডাটাবেজে কপি (একবার)
প্রজেক্ট ফোল্ডারে টার্মিনাল খুলুন:
```
vercel login
vercel link
vercel env pull .env.vercel
```
তারপর `.env.vercel` ফাইল থেকে `DATABASE_URL`-এর লাইনটা কপি করুন। আপনার `.env` ফাইলের একদম নিচে নাম বদলে বসান:
```
CLOUD_DATABASE_URL=postgresql://...
```
এরপর চালান:
```
python manage.py clone_to_cloud
```
জিজ্ঞেস করলে `yes` লিখুন। আপনার সব পেজ, ব্লগ, সেটিংস, ইউজার আর ছবি কপি হয়ে যাবে।
শেষে `.env.vercel` ফাইলটা মুছে দিন (এতে গোপন লিংক আছে)।

## ধাপ ৪ — আবার Deploy
Vercel → **Deployments** → সর্বশেষটার **⋯ → Redeploy**।
১–২ মিনিটে সাইট লাইভ হবে: `https://ektiarsoft.vercel.app` (বা Vercel যে নাম দেয়)।
লগইন করবেন আপনার এখনকার ইউজারনেম আর পাসওয়ার্ড দিয়েই।

তারপর **Settings → Environment Variables**-এ `SITE_URL` = আপনার লাইভ লিংক যোগ করে আরেকবার Redeploy করুন।

---

## পরে কোড বদলালে
```
git add -A
git commit -m "কী বদলালেন"
git push
```
Push করলেই Vercel নিজে থেকে নতুন ভার্সন লাইভ করবে।
নতুন migration থাকলে (ডাটাবেজের গঠন বদলালে), push-এর আগে চালান:
`set DATABASE_URL=<.env-এর CLOUD_DATABASE_URL>` → `python manage.py migrate` → `set DATABASE_URL=`

## নিজের ডোমেইন (যেমন ektiarsoft.com)
Vercel → **Settings → Domains → Add**। তারপর Environment Variables-এ যোগ করুন:
`ALLOWED_HOSTS=ektiarsoft.com,www.ektiarsoft.com`, `CSRF_TRUSTED_ORIGINS=https://ektiarsoft.com,https://www.ektiarsoft.com`, `SITE_URL=https://ektiarsoft.com`। শেষে Redeploy করুন।

## জেনে রাখুন
- লাইভ সাইটে ছবি আপলোড সর্বোচ্চ **4 MB** (Vercel-এর সীমা)। ফ্রি ডাটাবেজে 0.5 GB জায়গা, পোর্টফোলিওর জন্য যথেষ্ট।
- লাইভ সাইট আর কম্পিউটারের সাইট **আলাদা**। লাইভ ড্যাশবোর্ডে যা বদলাবেন, সেটা কম্পিউটারে আসবে না।
- `clone_to_cloud` **শুধু প্রথমবার** চালান। পরে চালালে লাইভ সাইটের ডাটা লোকাল কপি দিয়ে **বদলে যাবে**।
- পরে চাইলে ছবি Cloudinary-তে রাখা যায়: Vercel-এ `CLOUDINARY_URL` যোগ করলেই হবে।

## Image to Text: AI Mode চালু করা (ঐচ্ছিক, খরচ আছে)
1. https://console.anthropic.com → অ্যাকাউন্ট খুলুন → **Billing**-এ ক্রেডিট যোগ করুন → **API Keys → Create Key**
2. Vercel → **Settings → Environment Variables** → `ANTHROPIC_API_KEY` = আপনার key (Production + Preview)
3. ঐচ্ছিক: `OCR_AI_DAILY_LIMIT` (প্রতি ইউজারের দৈনিক সীমা, ডিফল্ট 30), `OCR_AI_MODEL` (ডিফল্ট `claude-opus-5-5`; সস্তা চাইলে `claude-haiku-5-5`)
4. Redeploy করুন

খরচ আনুমানিক: Opus প্রতি ছবি ~$0.03–0.06, Haiku প্রতি ছবি ~$0.001-এর কম। AI Mode শুধু লগইন করা ইউজার পায়।
ছবি AI-এর কাছে পাঠানো হয় (Anthropic), কিন্তু ছবি বা লেখা এই সাইটে সেভ হয় না — শুধু দৈনিক ব্যবহারের সংখ্যা রাখা হয়।
