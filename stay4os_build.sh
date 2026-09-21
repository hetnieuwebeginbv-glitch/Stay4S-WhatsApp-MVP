#!/bin/bash
# Stay4OS Automated Build Script
# Run on RunPod pod after repo sync completes
set -e

SOURCE=~/android/stay4os
KEYS=/workspace/stay4os-keys
DEVICE_TREE=/workspace/stay4os-device-tree
LOG=/workspace/stay4os_build.log

echo "=== STAY4OS BUILD START $(date) ===" | tee $LOG

# Step 1: Apply Stay4S device tree
echo "[1/6] Applying Stay4S device tree..." | tee -a $LOG
cp -r $DEVICE_TREE/device/google/tegu/* $SOURCE/device/google/tegu/ 2>>$LOG || true
cp -r $DEVICE_TREE/vendor/stay4s $SOURCE/vendor/ 2>>$LOG || true
echo "[1/6] Done" | tee -a $LOG

# Step 2: Setup build environment
echo "[2/6] Setting up build environment..." | tee -a $LOG
cd $SOURCE
export PATH=~/bin:$PATH
export USE_CCACHE=1
export CCACHE_EXEC=/usr/bin/ccache
ccache -M 100G 2>>$LOG || true
source build/envsetup.sh 2>>$LOG
echo "[2/6] Done" | tee -a $LOG

# Step 3: Breakfast tegu
echo "[3/6] Breakfast tegu..." | tee -a $LOG
breakfast tegu 2>>$LOG || {
  echo "[3/6] breakfast failed - may need vendor blobs first" | tee -a $LOG
  echo "[3/6] Attempting extract-files..." | tee -a $LOG
  cd $SOURCE/device/google/tegu
  if [ -f extract-files.sh ]; then
    ./extract-files.sh 2>>$LOG || true
  elif [ -f extract-files.py ]; then
    python3 extract-files.py 2>>$LOG || true
  fi
  cd $SOURCE
  source build/envsetup.sh 2>>$LOG
  breakfast tegu 2>>$LOG || {
    echo "[3/6] FAILED - cannot continue without device tree" | tee -a $LOG
    exit 1
  }
}
echo "[3/6] Done" | tee -a $LOG

# Step 4: Build with signing keys
echo "[4/6] Building Stay4OS (this takes 4-8 hours)..." | tee -a $LOG
export SIGNING_KEY_DIR=$KEYS
croot
brunch tegu 2>>$LOG || {
  echo "[4/6] Build FAILED" | tee -a $LOG
  tail -50 $LOG
  exit 1
}
echo "[4/6] BUILD COMPLETE!" | tee -a $LOG

# Step 5: Copy output
echo "[5/6] Copying build output..." | tee -a $LOG
mkdir -p /workspace/stay4os-output
cp $OUT/*.img /workspace/stay4os-output/ 2>>$Log || true
cp $OUT/*.zip /workspace/stay4os-output/ 2>>$Log || true
ls -lh /workspace/stay4os-output/ | tee -a $LOG
echo "[5/6] Done" | tee -a $LOG

# Step 6: Generate checksums
echo "[6/6] Generating checksums..." | tee -a $LOG
cd /workspace/stay4os-output
sha256sum * | tee -a $LOG
echo "=== STAY4OS BUILD EINDE $(date) ===" | tee -a $LOG
echo "STAY4OS_BUILD_COMPLETE" | tee -a $LOG