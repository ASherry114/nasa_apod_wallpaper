#!/bin/zsh

img_path=$1
scipt_contents="tell application \"System Events\"
    tell every desktop
        set picture to \"${img_path}\"
    end tell
end tell"
osascript -e ${scipt_contents}
