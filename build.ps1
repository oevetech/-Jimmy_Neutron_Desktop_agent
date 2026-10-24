# Gera o pet e o instalador em dist\
#   .\build.ps1
# Precisa de: Python 3 com PyQt6 e PyInstaller (pip install PyQt6 pyinstaller)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "1/2  Gerando dist\JimmyNeutronPet.exe ..."
python -m PyInstaller --noconfirm JimmyNeutronPet.spec
if ($LASTEXITCODE -ne 0) { throw "Falhou ao gerar o pet" }

Write-Host "2/2  Gerando dist\Instalar Jimmy Neutron Pet.exe ..."
python -m PyInstaller --noconfirm --onefile --windowed --name "Instalar Jimmy Neutron Pet" `
    --icon "$PSScriptRoot\assets\jimmy.ico" --workpath build\instalador --specpath build\instalador `
    --add-data "$PSScriptRoot\dist\JimmyNeutronPet.exe;." `
    --add-data "$PSScriptRoot\assets\instalador_jimmy.png;." `
    --add-data "$PSScriptRoot\assets\jimmy.ico;." `
    instalador_jimmy.py
if ($LASTEXITCODE -ne 0) { throw "Falhou ao gerar o instalador" }

Write-Host "Pronto: dist\JimmyNeutronPet.exe e dist\Instalar Jimmy Neutron Pet.exe"
