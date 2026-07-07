#!/bin/bash
set -e

# Make sure we are running in the correct directory
cd "$(dirname "$0")"

echo "=== 1. Cleaning old build artifacts ==="
rm -rf build dist dmg_stage LuaToolsHelper.dmg venv_build

echo "=== 2. Creating Python 3.14 virtual environment ==="
/opt/homebrew/bin/python3 -m venv venv_build
source venv_build/bin/activate

echo "=== 3. Installing PyInstaller in virtual environment ==="
pip install --upgrade pip
pip install pyinstaller

echo "=== 4. Compiling Python script to macOS App Bundle ==="
pyinstaller \
    --windowed \
    --name="LuaToolsHelper" \
    --icon="icon-windowed.icns" \
    --onedir \
    --clean \
    --noconfirm \
    luatools_helper.py

echo "=== 5. Deactivating virtual environment ==="
deactivate
rm -rf venv_build

echo "=== 6. Creating DMG staging directory ==="
mkdir -p dmg_stage
cp -R dist/LuaToolsHelper.app dmg_stage/

echo "=== 7. Creating drag-and-drop Applications link ==="
ln -s /Applications dmg_stage/Applications

echo "=== 8. Packaging staging directory into DMG ==="
hdiutil create \
    -volname "LuaToolsHelper" \
    -srcfolder dmg_stage \
    -ov \
    -format UDZO \
    LuaToolsHelper.dmg

echo "=== 9. Cleaning up staging area ==="
rm -rf dmg_stage
rm -rf build

echo "=== Build Complete! ==="
echo "You can find your installer at: $(pwd)/LuaToolsHelper.dmg"
