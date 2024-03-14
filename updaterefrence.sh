printf "\n"
printf "==============================================================\n"
printf "*************** CBI UPDATE REALTIME REFRENCES ****************\n"
printf "==============================================================\n"
printf "Note : Please backup folder app first!!!!!!!!!!!!!!!!!!!!!!!!!\n"
printf "\n"
read -p "Personal Access Token: " token
if [ -z "$token" ]
then
  token="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"
fi

read -p "Branch (main): " branch
if [ -z "$branch" ]
then
  branch="main"
fi

read -p "Username (cbi): " username
if [ -z "$username" ]
then
  username="cbi"
fi

read -s -p "Password (cbipa55word): " password
if [ -z "$password" ]
then
  password="cbipa55word"
fi

cd ~
rm -fr dtlogger
git clone "https://${token}@github.com/acepahmads/dtlogger.git"
cd dtlogger
git checkout "${branch}"
echo "$password" | sudo -S chmod +x /$folder/*
cd ~/.config
mkdir -p autostart
cp -f ~/dtlogger/rundbprocess.desktop ~/.config/autostart
cp -f ~/dtlogger/models.py ~/app/instrumen/datalogger/models/

