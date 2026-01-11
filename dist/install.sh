echo "installing UHC Osint"
sudo chmod 644 ./uhc-osint
chmod +x ./uhc-osint
sudo cp ./uhc-osint /usr/bin
mkdir -p ~/.local/share/applications
cat <<EOF > ~/.local/share/applications/uhc-osint.desktop
[Desktop Entry]
Type=Application
Name=UHC Osint
Comment=Perform Open Source Intelligence attacks, with everything you need in one app.
Exec=uhc-osint
Terminal=false
Categories=Other;Utility;Recon
EOF
