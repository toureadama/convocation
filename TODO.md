 Fix PDF Generation on Render - LibreOffice Headless Issue
# Status: ✅ PLAN APPROVED | ⏳ IN PROGRESS

## Current Task: Resolve 'source file could not be loaded' error in convocation_mysql.py on Render

### ✅ Completed Steps
- [x] Analyzed logs/files (convocation_mysql.py, app.py, Dockerfile, render.yaml)
- [x] Created detailed edit plan with absolute paths, permissions, fallbacks
- [x] User approved plan ✅

### ⏳ In Progress / Pending Steps
- [✅] **1. Update convocation_mysql.py** (absolute paths, chmod, env, fallback LO cmd)
  - ✅ Use absolute `/app/output`
  - ✅ Add `os.chmod(docx_path, 0o666)` before LO
  - ✅ Improve fallback without xvfb-run + simpler flags
  - ✅ Verify file size >1000 bytes
- [✅] **2. Update Dockerfile** (build-time verification, ENV LO_PATH/TMPDIR/FONTCONFIG)
- [✅] **3. Update render.yaml** (remove runtime apt/shell, add env vars, PORT=10000)
- [✅] **4. Local testing** (test_pdf_generation.py created w/ mocks)
- [✅] **5. Deploy to Render**
  - ✅ Commit `39cfb610` pushed to main
  - ⏳ Monitor Render logs (auto-deploy triggered)
- [⏳] **6. Production verification**
  - ⏳ Wait Render rebuild (~2-5 min), then test /api/generate
  - ⏳ Check no 500 errors

### 🔧 Key Changes Summary
```
convocation_mysql.py: _convert_with_libreoffice()
├── 📁 output_dir → Path('/app/output').absolute()
├── 🔐 os.chmod(docx_path, 0o666)
├── 🛡️ env HOME=/root, /tmp writable
├── 🔄 Fallback: direct libreoffice --convert-to pdf
└── ✅ Verify pdf.stat().st_size > 1000 bytes

Dockerfile/render.yaml: Build-time LO install + verification
```

### 📋 Rollback Plan
If issues: `git revert HEAD`

**Next Action: Edit convocation_mysql.py → Confirm → Proceed**

