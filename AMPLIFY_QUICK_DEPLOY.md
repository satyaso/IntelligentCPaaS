# AI-CPaaS Demo - AWS Amplify Quick Deploy

**Easiest Deployment Method** ⚡  
**Time**: 10-15 minutes  
**Result**: Public HTTPS URL  
**Cost**: ~$15-30/month

---

## Why Amplify?

✅ **Easiest**: Connect Git → Click Deploy → Done  
✅ **Fastest**: Live in 10-15 minutes  
✅ **Auto-deploy**: Git push = auto-deploy  
✅ **HTTPS Free**: SSL certificate included  
✅ **No server management**: Fully managed  

---

## Quick Start (3 Steps)

### Step 1: Add Amplify Config (2 minutes)

Create `amplify.yml` in your project root:

```yaml
version: 1
backend:
  phases:
    build:
      commands:
        - echo "Using existing AWS infrastructure"
frontend:
  phases:
    preBuild:
      commands:
        - pip3 install --upgrade pip
        - pip3 install -r requirements.txt
    build:
      commands:
        - python3 -c "from src.ai_cpaas_demo.data.data_seeder import DataSeeder; DataSeeder().seed_all()"
  artifacts:
    baseDirectory: /
    files:
      - '**/*'
  cache:
    paths:
      - '/root/.cache/pip/**/*'
```

Create `start.sh`:

```bash
#!/bin/bash
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 src.ai_cpaas_demo.web.app:app
```

Add to `requirements.txt`:
```
gunicorn==21.2.0
```

Commit and push:
```bash
chmod +x start.sh
git add amplify.yml start.sh requirements.txt
git commit -m "Add Amplify config"
git push origin main
```

### Step 2: Deploy on Amplify (5 minutes)

1. **Open AWS Console** → **AWS Amplify**
2. Click **"New app"** → **"Host web app"**
3. **Connect GitLab**:
   - Select `satyaso/appliedai-cpaas`
   - Branch: `main`
4. **Add Environment Variables**:
   ```
   AWS_REGION=us-east-1
   AWS_ACCOUNT_ID=378318846552
   DYNAMODB_RATE_LIMITS_TABLE=ai-cpaas-rate-limits
   DYNAMODB_DELIVERY_TRACKING_TABLE=ai-cpaas-delivery-tracking
   FLASK_ENV=production
   PORT=8080
   ```
5. **Create/Select Service Role** with:
   - `AmazonDynamoDBFullAccess`
   - `AmazonSESFullAccess`
6. Click **"Save and deploy"**

### Step 3: Access Your Demo (5-10 minutes)

Wait for deployment to complete, then:

**Your URL**: `https://main.xxxxx.amplifyapp.com`

🎉 **Done! Your demo is live!**

---

## Auto-Deploy

Every time you push to Git:

```bash
git push origin main
```

Amplify automatically:
1. Detects the push
2. Builds your app
3. Deploys to production
4. Updates live URL

**No manual steps needed!**

---

## Add Custom Domain (Optional)

1. **Amplify Console** → **"Domain management"**
2. Add domain: `demo.yourdomain.com`
3. Update DNS with provided CNAME
4. Wait 5-30 minutes for SSL

**Result**: `https://demo.yourdomain.com`

---

## Monitoring

### View Logs
- **Amplify Console** → Your app → Latest build
- **CloudWatch** → `/aws/amplify/ai-cpaas-demo`

### View Metrics
- **Amplify Console** → **"Monitoring"**
- Request count, errors, latency

---

## Troubleshooting

### Build Fails?
1. Check build logs in Amplify Console
2. Verify all dependencies in `requirements.txt`
3. Check environment variables are set

### App Won't Start?
1. Verify `start.sh` is executable: `chmod +x start.sh`
2. Check Gunicorn is in `requirements.txt`
3. Verify PORT environment variable is set

### AWS Permissions Error?
1. Go to **IAM** → **Roles** → Amplify service role
2. Attach `AmazonDynamoDBFullAccess`
3. Redeploy in Amplify Console

---

## Cost Breakdown

- **Build**: $0.01/minute (~$0.10 per deploy)
- **Hosting**: ~$15-30/month (includes SSL, CDN, auto-scaling)
- **Total**: ~$15-30/month

**Much cheaper than EC2!**

---

## Amplify vs EC2 vs App Runner

| Feature | Amplify | EC2 | App Runner |
|---------|---------|-----|------------|
| Setup | 10 min | 45 min | 20 min |
| Difficulty | ⭐ Easy | ⭐⭐⭐ Hard | ⭐⭐ Medium |
| Auto-deploy | ✅ | ❌ | ✅ |
| HTTPS | ✅ Free | Manual | ✅ Free |
| Cost/month | $15-30 | $37-42 | $25-50 |
| Best for | Demos | Production | APIs |

**Recommendation**: Use Amplify for quick demos!

---

## Summary

**3 Simple Steps**:
1. Add `amplify.yml` and `start.sh` → Push to Git
2. Connect Amplify to GitLab → Click Deploy
3. Get public HTTPS URL → Share your demo!

**Time**: 10-15 minutes  
**Cost**: ~$15-30/month  
**Maintenance**: Zero (fully managed)  

🚀 **The easiest way to deploy your AI-CPaaS demo!**

---

## Next Steps

After deployment:
1. ✅ Test all features on live URL
2. ✅ Add custom domain (optional)
3. ✅ Set up staging environment
4. ✅ Share URL with stakeholders!

**Your demo is production-ready!**
