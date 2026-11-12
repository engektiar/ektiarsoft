# Vercel-এ লাইভ করার গাইড (ফ্রি)

ওয়েবসাইট চলবে **Vercel**-এ, ডাটাবেজ থাকবে **Neon**-এ (ফ্রি PostgreSQL), আর আপলোড করা ছবি থাকবে **Cloudinary**-তে।

```
GitHub (কোড) ──► Vercel (ওয়েবসাইট) ──► Neon (ডাটাবেজ)
                                   └──► Cloudinary (ছবি)
```

> ⚠️ Neon আর Cloudinary-র লিংক **পাসওয়ার্ডের মতো গোপন**। এগুলো কাউকে পাঠাবেন না, চ্যাটে বা GitHub-এ দেবেন না।
> শুধু আপনার কম্পিউটারের `.env` ফাইলে আর Vercel-এর Settings-এ বসাবেন।

---

## ধাপ ১ — Cloudinary লিংক নিন
1. https://console.cloudinary.com খুলে লগইন করুন।
2. **Settings (⚙️) → API Keys** খুলুন।
3. **API environment variable** কপি করুন। এটা দেখতে এমন: `CLOUDINARY_URL=cloudinary://123456789:AbCdEf@your-cloud-name`
4. Notepad-এ রেখে দিন।

## ধাপ ২ — Neon ডাটাবেজ বানান
1. https://neon.tech-এ GitHub দিয়ে সাইন আপ করুন।
2. **Create project**:
   - Project name: `ektiarsoft`
   - Database name: `portfolio`
   - Region: **Singapore** (বাংলাদেশের সবচেয়ে কাছে)
3. **Connection string** কপি করুন। **"Pooled connection"** অপশন **চালু** রাখবেন (লিংকে `-pooler` লেখা থাকবে)।
   এটা দেখতে এমন: `postgresql://user:pass@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/portfolio?sslmode=require`

## ধাপ ৩ — আপনার এখনকার সাইট ক্লাউডে কপি করুন (একবার)
1. প্রজেক্ট ফোল্ডারের `.env` ফাইল খুলুন। একদম নিচে এই দুই লাইনের সামনের `#` মুছে লিংক বসান:
   ```
   CLOUD_DATABASE_URL=postgresql://...আপনার Neon লিংক...
   CLOUDINARY_URL=cloudinary://...আপনার Cloudinary লিংক...
   ```
   (`CLOUDINARY_URL=` দুবার লিখবেন না। Cloudinary থেকে কপি করা লেখার শুরুতে এটা থাকলে একবারই রাখুন।)
2. টার্মিনালে চালান:
   ```
   cd f:\xampp\htdocs\Portfolio
   python manage.py clone_to_cloud
   ```
3. জিজ্ঞেস করলে `yes` লিখে Enter চাপুন। এটা আপনার সব পেজ, ব্লগ, সেটিংস, ইউজার আর ছবি Neon আর Cloudinary-তে কপি করবে।
   আপনার কম্পিউটারের ডাটা যেমন আছে তেমনই থাকবে, কিছু মুছবে না।

## ধাপ ৪ — Vercel-এ প্রজেক্ট যোগ করুন
1. https://vercel.com-এ **GitHub দিয়ে** সাইন আপ করুন।
2. **Add New… → Project** চাপুন, তারপর `engektiar/ektiarsoft` repository-র পাশে **Import** চাপুন।
3. **Framework Preset:** `Other`। Build বা Output সেটিংসে হাত দেবেন না।
4. **Environment Variables**-এ এই ৩টা যোগ করুন:

   | Name | Value |
   |---|---|
   | `SECRET_KEY` | একটা লম্বা র‍্যান্ডম লেখা (নিচের কমান্ড দিয়ে বানান) |
   | `DATABASE_URL` | Neon লিংক (ধাপ ২) |
   | `CLOUDINARY_URL` | `cloudinary://...` অংশটুকু (ধাপ ১) |

   `SECRET_KEY` বানাতে টার্মিনালে চালান:
   ```
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
5. **Deploy** চাপুন। ১–২ মিনিট পর আপনার সাইট লাইভ হবে: `https://ektiarsoft.vercel.app` (বা Vercel যে নাম দেয়)।

## ধাপ ৫ — সাইট দেখুন আর SITE_URL সেট করুন
1. লাইভ লিংক খুলে দেখুন। লগইন করবেন আপনার এখনকার ইউজারনেম আর পাসওয়ার্ড দিয়েই।
2. Vercel → **Settings → Environment Variables**-এ যোগ করুন:
   `SITE_URL` = `https://ektiarsoft.vercel.app` (আপনার আসল লিংক)
3. **Deployments → ⋯ → Redeploy** চাপুন।

---

## পরে কোড বদলালে
```
git add -A
git commit -m "কী বদলালেন"
git push
```
Push করলেই Vercel নিজে থেকে নতুন ভার্সন লাইভ করবে।

**নতুন migration থাকলে** (ডাটাবেজের গঠন বদলালে), push করার আগে চালান:
```
set DATABASE_URL=...আপনার Neon লিংক...
python manage.py migrate
set DATABASE_URL=
```

## নিজের ডোমেইন (যেমন ektiarsoft.com)
1. Vercel → **Settings → Domains → Add** → ডোমেইন লিখুন। Vercel যে DNS রেকর্ড দেখাবে, সেটা ডোমেইন কেনার সাইটে বসান।
2. Environment Variables-এ যোগ করুন:
   - `ALLOWED_HOSTS` = `ektiarsoft.com,www.ektiarsoft.com`
   - `CSRF_TRUSTED_ORIGINS` = `https://ektiarsoft.com,https://www.ektiarsoft.com`
   - `SITE_URL` = `https://ektiarsoft.com`
3. Redeploy করুন।

## জেনে রাখুন
- **লাইভ সাইটে ছবি আপলোড সর্বোচ্চ 4 MB।** এটা Vercel-এর সীমা।
- কিছুক্ষণ কেউ না এলে প্রথমবার সাইট খুলতে ১–৩ সেকেন্ড বেশি লাগতে পারে।
- লাইভ সাইটে ড্যাশবোর্ড থেকে যা বদলাবেন, সেটা Neon-এ সেভ হবে। আপনার কম্পিউটারের লোকাল সাইটে সেটা আসবে না, দুটো আলাদা।
- `clone_to_cloud` **শুধু প্রথমবার** চালান। পরে চালালে লাইভ সাইটের ডাটা আবার লোকাল কপি দিয়ে **বদলে যাবে**।
