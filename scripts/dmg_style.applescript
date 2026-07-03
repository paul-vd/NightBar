-- Style the mounted DMG window: icon view, background image, big icons,
-- NightBar on the left and the Applications shortcut on the right.
-- Positions must match assets/make_dmg_bg.py (NB_X/APP_X/ICON_Y).
on run argv
	set volName to item 1 of argv
	tell application "Finder"
		tell disk volName
			open
			set current view of container window to icon view
			set toolbar visible of container window to false
			set statusbar visible of container window to false
			-- {left, top, right, bottom}; content ~= 640 x 400
			set the bounds of container window to {300, 150, 940, 570}
			set opts to the icon view options of container window
			set arrangement of opts to not arranged
			set icon size of opts to 112
			set background picture of opts to file ".background:dmg_bg.png"
			set position of item "NightBar.app" of container window to {150, 200}
			set position of item "Applications" of container window to {490, 200}
			update without registering applications
			delay 1
			close
		end tell
	end tell
end run
