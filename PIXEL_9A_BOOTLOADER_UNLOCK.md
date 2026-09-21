# Pixel 9a Bootloader Unlock Guide -- Stay4OS

## WAARSCHUWING
Bootloader unlock vernietigt ALLE data op de telefoon!
Maak eerst een backup als je iets wilt behouden.

## Voorbereiding
1. Zorg dat adb en fastboot op je laptop staan
2. Pixel 9a verbonden via USB
3. Batterij > 50%
4. Alle belangrijke data gebackupt

## Stap 1: Developer options
1. Settings > About phone > Build number
2. Tik 7 keer op Build number
3. Settings > System > Developer options
4. Enable: OEM unlocking
5. Enable: USB debugging

## Stap 2: Bootloader unlock
```bash
# Start in fastboot mode
adb reboot bootloader

# Controleer device
fastboot devices

# Unlock bootloader (vernietigt alle data!)
fastboot flashing unlock

# Bevestig op het scherm met volume knoppen
```

## Stap 3: Na unlock
- Device doet factory reset
- Setup opnieuw (maar installeer GEEN Google account)
- GrapheneOS is nu weg -- we gaan Stay4OS flashen

## Stap 4: Stay4OS flashen
```bash
# Start in fastboot mode
adb reboot bootloader

# Flash Stay4OS images
fastboot flash boot boot.img
fastboot flash system system.img
fastboot flash vendor vendor.img
fastboot flash vendor_boot vendor_boot.img
fastboot flash product product.img
fastboot flash system_ext system_ext.img

# Flash vbmeta met eigen keys (disable verity voor eerste test)
fastboot flash vbmeta vbmeta.img --disable-verity --disable-verification

# Reboot
fastboot reboot
```

## Stap 5: Verified boot
Na succesvolle test build:
```bash
# Flash vbmeta ZONDER --disable-verity (full verified boot)
fastboot flash vbmeta vbmeta.img
fastboot reboot
```

Verified boot status: YELLOW (custom key, niet Google)

## Stap 6: Lock bootloader (optioneel, pas na stabiele build)
```bash
adb reboot bootloader
fastboot flashing lock
```

## Rollback
Als Stay4OS niet boot:
```bash
# Start in fastboot mode (hold volume down + power)
fastboot flash boot stock_boot.img
fastboot flash system stock_system.img
# ... alle stock images
fastboot reboot
```