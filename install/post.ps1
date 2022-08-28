if (!$DIR){
    "Why are you trying to run this script outside of scoop? get outta here"
    "You can install Smoothie with the following command: iex(irm tl.ctt.cx);Get Smoothie"
    pause;exit
}


Rename-Item -Path (Convert-Path "$DIR\Smoothie*") -NewName "Smoothie"

if (-Not(Test-Path "$ScoopDir\shims\sm.exe")){
    Copy-Item "$ScoopDir\shims\7z.exe" "$ScoopDir\shims\sm.exe" # All shims are the same
}
if (-Not(Test-Path "$ScoopDir\shims\sm.shim")){

    New-Item "$ScoopDir\shims\sm.shim" -Force
    Add-Content "$ScoopDir\shims\sm.shim" "path = `"$DIR\VapourSynth\python.exe`"$([Environment]::NewLine)args = `"$DIR\Smoothie\Smoothie.py`""
}

Invoke-RestMethod tl.ctt.cx | Invoke-Expression

$rc = (Get-Content "$DIR\Smoothie\settings\recipe.ini") -replace ('libx264 -preset slow -crf 15',(Get-EncodingArgs))

if ($valid_args -like "*libx26*"){
    $rc = $rc -replace ('gpu=true','gpu=false')
}

Set-Content "$DIR\Smoothie\settings\recipe.ini" -Value $rc

$SendTo = [System.Environment]::GetFolderPath('SendTo')

Remove-Item "$SendTo\Smoothie.lnk" -Force -Ea Ignore

if (-Not(Test-Path "$DIR\sm.ico")){
    Invoke-WebRequest -UseBasicParsing https://cdn.discordapp.com/attachments/885925073851146310/940709737685725276/sm.ico -OutFile "$DIR\sm.ico"
}
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$SendTo\smoothie.lnk")
$Shortcut.TargetPath = "$DIR\VapourSynth\python.exe"
$Shortcut.Arguments = "$DIR\Smoothie\smoothie.py -input"
$Shortcut.IconLocation = "$DIR\sm.ico"
$Shortcut.Save()
Rename-Item -Path "$SendTo\smoothie.lnk" -NewName 'Smoothie.lnk' # Shortcuts are always created in lowercase for some reason


