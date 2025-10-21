# Project Cleanup Plan

## Current State Analysis

The project has grown organically and contains:
- ✅ **Core application** (`pwa-dobot-plc/`)
- ✅ **Working solution** (alarm clearing fix)
- ✅ **Documentation** (multiple guides and summaries)
- ✅ **Test files** (scattered in root)
- ✅ **Migration artifacts** (official API files)
- ✅ **Deployment scripts** (multiple versions)

## Proposed Clean Structure

```
rpi-dobot/
├── app/                          # Main application
│   └── pwa-dobot-plc/           # (keep as-is - working app)
├── docs/                        # All documentation
│   ├── guides/                  # Setup and usage guides
│   ├── solutions/              # Problem resolution docs
│   └── api/                     # API documentation
├── scripts/                     # All executable scripts
│   ├── deployment/              # Deployment scripts
│   ├── testing/                 # Test scripts
│   └── migration/               # Migration utilities
├── lib/                         # External libraries
│   └── DobotAPI/               # Official Dobot API files
├── tests/                       # All test files
└── README.md                    # Main project readme
```

## File Categorization

### 📁 Core Application (KEEP AS-IS)
```
pwa-dobot-plc/                   # ✅ Working application - DO NOT TOUCH
├── backend/                     # ✅ Active backend
├── frontend/                    # ✅ Active frontend  
├── deploy/                      # ✅ Deployment configs
└── README.md                    # ✅ App-specific docs
```

### 📁 Documentation to Organize
```
docs/
├── guides/
│   ├── DEPLOY_TO_PI.md
│   ├── PLC_DB1_Setup_Guide.md
│   ├── PLC_Robot_Control_Guide.md
│   ├── PLC_Settings_Guide.md
│   └── QUICK_START_ON_PI.md
├── solutions/
│   ├── SOLUTION_SUMMARY.md
│   ├── BUGFIX_SUMMARY.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   └── DOBOT_FIX_COMPLETE_DOCUMENTATION.md
├── api/
│   ├── DOBOT_API_MIGRATION_PLAN.md
│   ├── OFFICIAL_API_MIGRATION_GUIDE.md
│   ├── OFFICIAL_API_QUICK_REFERENCE.md
│   └── example_README.md
└── index/
    └── DOCUMENTATION_INDEX.md
```

### 📁 Scripts to Organize
```
scripts/
├── deployment/
│   ├── setup.sh
│   ├── FINAL_DEPLOYMENT.sh
│   ├── setup_official_dobot_api.sh
│   └── migrate_to_official_api.sh
├── testing/
│   ├── test_alarm_clear.py
│   ├── test_improved_client.py
│   ├── test_official_api_connection.py
│   ├── test_official_api_movement.py
│   └── test_official_api_peripherals.py
└── migration/
    └── deploy_official_api.sh
```

### 📁 Libraries to Organize
```
lib/
└── DobotAPI/                    # Official Dobot API files
    ├── DobotControl.py
    ├── DobotDll.dll
    ├── DobotDll.h
    ├── DobotDllType.py
    ├── msvcp120.dll
    ├── msvcr120.dll
    ├── Qt5Core.dll
    ├── Qt5Network.dll
    └── Qt5SerialPort.dll
```

### 📁 Test Files to Organize
```
tests/
├── pydobot/                     # Original pydobot tests
│   ├── test_dobot_go_lock.py
│   ├── test_dobot_home.py
│   ├── test_dobot_ptp_params.py
│   ├── test_dobot_simple.py
│   └── test_dobot_speed.py
└── official_api/               # Official API tests
    ├── test_official_api_connection.py
    ├── test_official_api_movement.py
    └── test_official_api_peripherals.py
```

## Files to Keep in Root
```
rpi-dobot/
├── README.md                    # Main project readme
├── Plan.md                     # Project planning
├── app-description.md          # App overview
└── PI_UPDATE_COMMANDS.md       # Quick reference
```

## Dependencies Analysis

### ✅ SAFE TO MOVE (No dependencies)
- All `.md` documentation files
- All test files (standalone)
- All deployment scripts
- DobotAPI library files

### ⚠️ CHECK BEFORE MOVING
- `pwa-dobot-plc/` - **DO NOT TOUCH** (active application)
- Any files referenced in `app.py` imports
- Any files referenced in deployment scripts

### 🔍 Files Referenced in Code
Let me check for any hardcoded paths in the application...

## Implementation Steps

### Phase 1: Create Directory Structure
```bash
mkdir -p docs/{guides,solutions,api,index}
mkdir -p scripts/{deployment,testing,migration}
mkdir -p lib
mkdir -p tests/{pydobot,official_api}
```

### Phase 2: Move Documentation
```bash
# Guides
mv DEPLOY_TO_PI.md docs/guides/
mv PLC_*_Guide.md docs/guides/
mv QUICK_START_ON_PI.md docs/guides/

# Solutions
mv SOLUTION_SUMMARY.md docs/solutions/
mv BUGFIX_SUMMARY.md docs/solutions/
mv IMPLEMENTATION_SUMMARY.md docs/solutions/
mv DOBOT_FIX_COMPLETE_DOCUMENTATION.md docs/solutions/

# API Documentation
mv DOBOT_API_MIGRATION_PLAN.md docs/api/
mv OFFICIAL_API_*.md docs/api/
mv example_README.md docs/api/

# Index
mv DOCUMENTATION_INDEX.md docs/index/
```

### Phase 3: Move Scripts
```bash
# Deployment scripts
mv setup.sh scripts/deployment/
mv FINAL_DEPLOYMENT.sh scripts/deployment/
mv setup_official_dobot_api.sh scripts/deployment/
mv migrate_to_official_api.sh scripts/migration/

# Test scripts
mv test_*.py tests/
```

### Phase 4: Move Libraries
```bash
mv DobotAPI/ lib/
```

### Phase 5: Update References
- Update any hardcoded paths in scripts
- Update documentation links
- Update README.md with new structure

## Benefits of This Organization

1. **Clear Separation**: App code vs docs vs scripts vs tests
2. **Easy Navigation**: Logical grouping by purpose
3. **Maintainable**: Easy to find and update files
4. **Professional**: Clean, organized structure
5. **Scalable**: Easy to add new files in appropriate locations

## Risk Mitigation

1. **Backup First**: Create git commit before moving files
2. **Test After**: Verify app still works after reorganization
3. **Update Paths**: Check for any broken references
4. **Document Changes**: Update README with new structure

## Files That Stay in Root

- `README.md` - Main project entry point
- `Plan.md` - Project planning document
- `app-description.md` - Quick app overview
- `PI_UPDATE_COMMANDS.md` - Quick reference
- `pwa-dobot-plc/` - **Core application (untouched)**

This keeps the root clean while preserving all functionality and making the project much more navigable.
