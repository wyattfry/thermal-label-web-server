## TODO

- [ ] extract hard coded configuration to a proper config file
- [ ] split single py file into a conventional python project structure
- [ ] update README.md with missing info, e.g. prerequisites, installing
- [ ] update web UI, make it minimal, see below
- [ ] a ps1 file to install, enable, disable, or uninstall it as a Windows service
- [ ] it should delete the file(s) after printing


## UI Redesign

When first visiting the page, it just says "Thermal Label Printer" centered at top, and below that, on the left, a big "Upload File to Print" button, and under that a hint text with accepted file extensions. On the right, a grayed out / disabled "Print" button. After uploading a file, the a preview is automatically displayed below the buttons, and on mobile, scaled to fit the remaining height and width of the screen. When "Print" is tapped / clicked, it disables the print button, has some progress message, then an outcome message, can be overlayed on the print preview. It disappears after a few seconds. The user can then click Print to print again, or Upload to upload a different file. Feel free to modify any of the above in the interest of simplicity. An alternative would be to keep the current design but hide everything except the Upload and Print buttons behind a collapsable "Advanced" button. That might be better than all the overly complex things above. Your call.