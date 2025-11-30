#!/bin/bash
# Cypress wrapper script for NixOS/Replit environment

# Find all relevant library paths from Nix store
LIB_PATHS=""

# Add paths from Nix Cypress package dependencies
for lib in mesa-libgbm libxkbcommon gtk3 pango cairo gdk-pixbuf atk at-spi2-atk at-spi2-core libdrm expat cups dbus alsa-lib nss nspr systemd glib; do
  paths=$(find /nix/store -maxdepth 2 -name "*-${lib}-*" -type d 2>/dev/null | head -1)
  if [ -n "$paths" ]; then
    for p in $paths; do
      if [ -d "$p/lib" ]; then
        LIB_PATHS="$LIB_PATHS:$p/lib"
      fi
      if [ -d "$p/lib64" ]; then
        LIB_PATHS="$LIB_PATHS:$p/lib64"
      fi
    done
  fi
done

# Add X11 libraries
for lib in libX11 libXcomposite libXdamage libXext libXfixes libXrandr libxcb libXcursor libXi libXrender libXScrnSaver libXtst xkeyboard-config; do
  paths=$(find /nix/store -maxdepth 2 -name "*-${lib}-*" -type d 2>/dev/null | head -1)
  if [ -n "$paths" ]; then
    for p in $paths; do
      if [ -d "$p/lib" ]; then
        LIB_PATHS="$LIB_PATHS:$p/lib"
      fi
    done
  fi
done

# Add gcc/glibc libs
for lib in glibc gcc; do
  paths=$(find /nix/store -maxdepth 2 -name "*-${lib}-*" -type d 2>/dev/null | head -1)
  if [ -n "$paths" ]; then
    for p in $paths; do
      if [ -d "$p/lib" ]; then
        LIB_PATHS="$LIB_PATHS:$p/lib"
      fi
    done
  fi
done

export LD_LIBRARY_PATH="${LIB_PATHS#:}:$LD_LIBRARY_PATH"
export ELECTRON_DISABLE_SANDBOX=1

# Run Cypress using the npm-installed version
exec npx cypress "$@"
