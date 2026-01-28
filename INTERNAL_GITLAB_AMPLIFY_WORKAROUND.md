# Deploying from AWS Internal GitLab to Amplify

## Problem
AWS Amplify doesn't support AWS internal GitLab (`gitlab.aws.dev`). It only supports GitHub, GitLab.com, Bitbucket, and CodeCommit.

## Solution Options

### Option 1: Mirror to AWS CodeCommit (Recommended)

Set up automatic mirroring from internal GitLab to CodeCommit, then connect Amplify to CodeCommit.

#### Step 1: Create CodeCommit Repository

```bash
# Create CodeCommit repo
aws codecommit create-repository \
  --repository-name appliedai-cpaas \
  --repository-description "AI CPaaS Demo - Mirror from GitLab" \
  --region us-east-1

# Get clone URL
aws codecommit get-repository \
  --repository-name appliedai-cpaas \
  --region us-east-1 \
  --query 'repositoryMetadata.cloneUrlHttp'
```

#### Step 2: Set Up GitLab CI/CD Mirror

Add this to your `.gitlab-ci.yml` in the GitLab repo:

```yaml
mirror-to-codecommit:
  stage: deploy
  only:
    - main
  script:
    - git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/appliedai-cpaas
    - git push codecommit main --force
  tags:
    - aws
```

#### Step 3: Connect Amplify to CodeCommit

1. Go to AWS Amplify Console
2. Click "New app" → "Host web app"
3. Select "AWS CodeCommit"
4. Select repository: `appliedai-cpaas`
5. Select branch: `main`
6. Configure and deploy

**Pros**: Automatic sync, native Amplify support
**Cons**: Requires GitLab CI/CD setup

---

### Option 2: Manual Git Push to CodeCommit

Manually push to CodeCommit whenever you want to deploy.

#### Step 1: Add CodeCommit as Remote

```bash
# Add CodeCommit remote
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/appliedai-cpaas

# Push to CodeCommit
git push codecommit main
```

#### Step 2: Connect Amplify to CodeCommit

Same as Option 1, Step 3.

**Pros**: Simple, no CI/CD needed
**Cons**: Manual push required for each deployment

---

### Option 3: Use EC2 Instead of Amplify

Deploy directly to EC2 from internal GitLab (no Amplify needed).

#### Deploy Script

```bash
#!/bin/bash
# deploy-to-ec2.sh

# SSH into EC2 instance
ssh -i your-key.pem ec2-user@<instance-ip> << 'EOF'
  cd /home/ec2-user/appliedai-cpaas
  
  # Pull latest code from GitLab
  git pull origin main
  
  # Install dependencies
  pip3 install -r requirements.txt
  
  # Restart application
  sudo systemctl restart ai-cpaas-demo
EOF
```

**Pros**: Full control, works with internal GitLab
**Cons**: Manual server management

---

## Recommended Approach

For AWS internal GitLab, I recommend **Option 1 (Mirror to CodeCommit)** because:
- Automatic deployment on git push
- Native Amplify integration
- No manual steps after initial setup
- Keeps your internal GitLab as source of truth

## Quick Start: Mirror to CodeCommit

```bash
# 1. Create CodeCommit repo
aws codecommit create-repository \
  --repository-name appliedai-cpaas \
  --region us-east-1

# 2. Add CodeCommit as remote
git remote add codecommit https://git-codecommit.us-east-1.amazonaws.com/v1/repos/appliedai-cpaas

# 3. Push to CodeCommit
git push codecommit main

# 4. Go to Amplify Console and connect to CodeCommit repo
```

Now Amplify will deploy from CodeCommit, and you can set up GitLab CI/CD to auto-mirror changes.
