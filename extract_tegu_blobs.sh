#!/bin/bash
# Stay4S Vendor Blob Extraction Script for Pixel 9a (tegu)
# Run on a machine with adb connected to Pixel 9a
# Extracts proprietary blobs needed for AOSP build

VENDOR_DIR=vendor/google/tegu
BLOB_LIST=$VENDOR_DIR/proprietary-blobs.txt
EXTRACT_DIR=$VENDOR_DIR/proprietary

mkdir -p $EXTRACT_DIR

# List of required proprietary blobs for tegu
# Based on standard Pixel device blob lists
BLOBS=(
    # Camera
    /system/lib64/libgcam_hal3.so
    /system/lib64/libcamera_client.so
    /system/lib64/libcamera_metadata.so
    /system/lib64/libgui_shim.so
    
    # GPU/Graphics
    /vendor/lib64/egl/libGLES_mali.so
    /vendor/lib64/hw/vulkan.zumapro.so
    /vendor/lib64/libGLESv2.so
    /vendor/lib64/libGLESv3.so
    
    # Modem/Radio
    /vendor/lib64/libril.so
    /vendor/lib64/libreference-ril.so
    /vendor/lib64/libmtk-ril.so
    /vendor/firmware/modem.img
    
    # Sensors
    /vendor/lib64/hw/sensors.zumapro.so
    /vendor/lib64/sensors.zumapro.so
    
    # DRM
    /vendor/lib64/mediadrm
    /vendor/lib64/libwvdrm_L1.so
    /vendor/lib64/libwvhalf.so
    
    # GPS
    /vendor/lib64/hw/gps.zumapro.so
    /vendor/firmware/gps.bin
    
    # Bluetooth
    /vendor/lib64/hw/bluetooth.zumapro.so
    /vendor/firmware/bt.bin
    
    # WiFi
    /vendor/lib64/hw/wifi.zumapro.so
    /vendor/firmware/wifi.bin
    
    # Tensor G4 specific
    /vendor/lib64/libedgetpu.google.so
    /vendor/lib64/libtensorflow_google.so
    /vendor/lib64/hw/edgetpu.zumapro.so
)

echo "=== STAY4S VENDOR BLOB EXTRACTION ==="
echo "Device: Pixel 9a (tegu)"
echo "Target: $EXTRACT_DIR"
echo ""

# Check adb connection
if ! adb devices | grep -q "device$"; then
    echo "ERROR: No device connected via adb"
    exit 1
fi

# Extract each blob
COUNT=0
FAIL=0
for BLOB in "${BLOBS[@]}"; do
    if adb shell "ls $BLOB 2>/dev/null" | grep -q "$BLOB"; then
        DIR=$(dirname "$EXTRACT_DIR$BLOB")
        mkdir -p "$DIR"
        adb pull "$BLOB" "$EXTRACT_DIR$BLOB" 2>/dev/null
        if [ $? -eq 0 ]; then
            COUNT=$((COUNT + 1))
            echo "  OK: $BLOB"
        else
            FAIL=$((FAIL + 1))
            echo "  FAIL: $BLOB"
        fi
    else
        echo "  SKIP (not found): $BLOB"
    fi
done

echo ""
echo "=== EXTRACTION COMPLETE ==="
echo "Extracted: $COUNT | Failed: $FAIL | Total: ${#BLOBS[@]}"
echo "Output: $EXTRACT_DIR"
du -sh $EXTRACT_DIR 2>/dev/null