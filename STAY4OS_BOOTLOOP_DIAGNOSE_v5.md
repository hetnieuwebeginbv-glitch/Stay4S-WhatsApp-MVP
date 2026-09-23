# STAY4OS BOOTLOOP-DIAGNOSE v5 (23 sep 2026)

## Symptoom
Stay4OS v5 bootloopt: telefoon start de kernel maar komt nooit bij Android.
System_server/zygote starten nooit.

## Bewijs (console-ramoops, 558KB, 4552 regels)
- **106× dezelfde init-fout:**
  `init: Activation of cgroup controller +memory failed in path /sys/fs/cgroup/system/uid_1058: Invalid argument`
- **813× servicemanager-retry:** `android.security.maintenance could not be found`
- Geen system_server-start, geen zygote-start → boot stopt in init-fase

## KERNEL-CMDLINE (de oorzaak)
```
cgroup_disable=memmry   cgroup.memory=nokmem
cgroup: Disabling memory control group subsystem
```

## Diagnose: KERNEL/USERSPACE-MISMATCH
1. De **GrapheneOS-kernel** (Image.lz4 + dtb, gebruikt in v5) zet `cgroup_disable=memory`
   + `cgroup.memory=nokmem` in de kernel-cmdline/bootconfig
2. **Android init** (AOSP-userland) VEREIST memory-cgroups voor app-UID-paden
   (`/sys/fs/cgroup/system/uid_1058` — memory-controller)
3. Het systeem kan die cgroup niet activeren (Invalid argument) → init kan
   geen app-processen opzetten → system_server start nooit → bootloop

De v4/vroegere builds gebruikten de eigen kernel-build (boot.img 53MB met dtb)
die géén cgroup-disable had — daarom had de kernel wél een correcte boot.
De v5-build koos de GrapheneOS-kernel (voor de juiste hardware-dtb), maar die
kernel breekt de Android-cgroup-verwachtingen.

## Secundair probleem
`android.security.maintenance` AIDL-service ontbreekt in de build (vold
blijft proberen de lazy service te starten). Los hiervan op in de build.

## OPLOSSINGSROUTES
1. **Kernel-cmdline fixen** (aanbevolen): `cgroup_disable=memory` uit de
   bootconfig/vendor_kernel_boot halen → memory-cgroup aan → init kan
   app-UID-cgroups activeren
2. **Eigen kernel-build gebruiken** (niet GrapheneOS-kernel): boot.img 53MB
   met embedded dtb — de kernel die wél werkte, maar dan hardware-dtb-risico
3. **Bootconfig in vendor_kernel_boot.img aanpassen** (laagste risico):
   `cgroup.memory=nokmem` verwijderen

## VASTSTELLING
De dtb-match was CORRECT (DTBO match id 0x60b06, rev 0x10000, SOC DTB index 3)
— dus de kernel vond de hardware. De bootloop is NIET de dtb (zoals poging 1),
maar de cgroup-kernelconfig die de GrapheneOS-kernel meebrengt.

*OpenCode — 23 sep 2026. Op basis van stay4os_v5_bootloop.log (console-ramoops).*